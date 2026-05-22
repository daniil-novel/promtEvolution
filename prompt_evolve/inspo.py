"""INSPO-like instruction population evolution."""

from __future__ import annotations

from dataclasses import dataclass

from .evaluator import run_candidate
from .llm import generate_text
from .models import LLMProvider, PromptCandidate, PromptRunResult, RewardWeights, TestCase
from .prompts import PROMPT_ENGINEERING_TECHNIQUES, build_seed_prompt, generate_prompt_candidates, select_best_prompt
from .providers import FatalProviderError
from .rewards import reward_score
from .scope import generate_guidelines, update_prompt_with_guidelines
from .trajectories import ReplayBuffer, TrajectoryRecord


@dataclass
class InstructionGenome:
    candidate: PromptCandidate
    weight: float = 1.0
    reward: float = 0.0

    def to_dict(self) -> dict[str, float | str | int]:
        return {
            "id": self.candidate.id,
            "iteration": self.candidate.iteration,
            "weight": self.weight,
            "reward": self.reward,
        }


@dataclass
class InspoEvolutionResult:
    best: PromptRunResult
    population: list[InstructionGenome]
    replay_buffer: ReplayBuffer
    all_results: list[PromptRunResult]
    guidelines: list[dict[str, list[str]]]


def _normalize_population(population: list[InstructionGenome]) -> list[InstructionGenome]:
    if not population:
        return []
    total = sum(max(item.reward, 0.0) for item in population) or len(population)
    return [
        InstructionGenome(
            candidate=item.candidate,
            reward=item.reward,
            weight=max(item.reward, 0.0) / total if total else 1 / len(population),
        )
        for item in population
    ]


def reflect_failures(
    result: PromptRunResult,
    provider: LLMProvider,
    *,
    model: str | None = None,
    reasoning: str | None = None,
) -> list[str]:
    failed = [item.to_dict() for item in result.evaluations if not item.passed]
    if not failed:
        return ["Усиль стабильные правила, сохранив текущий формат и успешное поведение."]
    messages = [
        {
            "role": "system",
            "content": (
                "Ты LLM-оптимизатор INSPO. Проанализируй ошибки агента и верни короткие "
                "правила для новой инструкции. Пиши на русском."
            ),
        },
        {
            "role": "user",
            "content": f"Промпт:\n{result.candidate.content}\n\nОшибки:\n{failed}\n\nВерни 3-6 правил.",
        },
    ]
    try:
        text = generate_text(provider, messages, model=model, reasoning=reasoning)
    except FatalProviderError:
        raise
    except Exception:
        text = "\n".join(
            [
                "- Не отвечай без проверки обязательного формата.",
                "- Разделяй уверенные, сомнительные и ошибочные случаи.",
                "- Добавь явную самопроверку перед финальным ответом.",
            ]
        )
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip("- ").strip()][:6]


def mutate_instruction(
    parent: PromptRunResult,
    provider: LLMProvider,
    *,
    generation: int,
    child_index: int,
    model: str | None = None,
    reasoning: str | None = None,
) -> PromptCandidate:
    guidelines = generate_guidelines(parent, provider, model=model, reasoning=reasoning)
    reflections = reflect_failures(parent, provider, model=model, reasoning=reasoning)
    seed = update_prompt_with_guidelines(parent.candidate.content, guidelines)
    messages = [
        {
            "role": "system",
            "content": (
                "Ты optimizer для production system prompts. Создай новую версию инструкции "
                "по принципу INSPO: instruction-policy co-evolution. Верни только Markdown-промпт."
            ),
        },
        {
            "role": "user",
            "content": (
                "<parent_prompt>\n"
                f"{seed}\n"
                "</parent_prompt>\n\n"
                "<reflection>\n"
                + "\n".join(f"- {item}" for item in reflections)
                + "\n</reflection>\n\n"
                f"{PROMPT_ENGINEERING_TECHNIQUES}\n\n"
                "Сделай промпт строже, проверяемее и устойчивее к ошибкам."
            ),
        },
    ]
    try:
        content = generate_text(provider, messages, model=model, reasoning=reasoning)
    except FatalProviderError:
        raise
    except Exception:
        content = seed
    return PromptCandidate(id=f"generation_{generation}_child_{child_index}", content=content, iteration=generation)


def run_inspo_evolution(
    *,
    task: str,
    baseline_prompt: str | None,
    testcases: list[TestCase],
    provider: LLMProvider,
    population_size: int,
    generations: int,
    elite_size: int = 2,
    replay_buffer_size: int = 100,
    model: str | None = None,
    reasoning: str | None = None,
    self_check: bool = True,
    llm_evaluate: bool = True,
    status: callable | None = None,
) -> InspoEvolutionResult:
    initial = generate_prompt_candidates(
        task,
        baseline_prompt or build_seed_prompt(task),
        provider,
        count=population_size,
        iteration=1,
        model=model,
        reasoning=reasoning,
    )
    population = [InstructionGenome(candidate=item) for item in initial]
    replay = ReplayBuffer(max_size=replay_buffer_size)
    all_results: list[PromptRunResult] = []
    all_guidelines: list[dict[str, list[str]]] = []
    best_result: PromptRunResult | None = None

    for generation in range(1, generations + 1):
        if status:
            status(f"[6/10] Generation {generation}/{generations}: evaluating population...")
        evaluated: list[tuple[InstructionGenome, PromptRunResult]] = []
        for genome_index, genome in enumerate(population, start=1):
            if status:
                status(
                    f"  - Generation {generation}/{generations}, "
                    f"candidate {genome_index}/{len(population)}: {genome.candidate.id}"
                )
            result = run_candidate(
                genome.candidate,
                testcases,
                provider,
                model=model,
                reasoning=reasoning,
                self_check=self_check,
                llm_evaluate=llm_evaluate,
                status=status,
            )
            reward = reward_score(result, weights=RewardWeights())
            if status:
                status(f"  - {genome.candidate.id}: reward={reward:.3f}")
            replay.add(TrajectoryRecord.from_result(generation=generation, result=result, reward=reward))
            updated = InstructionGenome(candidate=genome.candidate, reward=reward, weight=reward)
            evaluated.append((updated, result))
            all_results.append(result)
        evaluated.sort(key=lambda item: item[0].reward, reverse=True)
        generation_best = evaluated[0][1]
        best_result = select_best_prompt([generation_best] + ([best_result] if best_result else []))
        if status:
            status(f"[6/10] Generation {generation}/{generations}: generating guidelines...")
        all_guidelines.append(generate_guidelines(generation_best, provider, model=model, reasoning=reasoning))

        elites = [item[0] for item in evaluated[: max(1, elite_size)]]
        next_population = list(elites)
        child_index = 1
        while len(next_population) < population_size:
            if status:
                status(
                    f"[6/10] Generation {generation}/{generations}: "
                    f"mutating child {child_index}/{population_size - len(elites)}"
                )
            parent_result = evaluated[(child_index - 1) % len(evaluated)][1]
            child = mutate_instruction(
                parent_result,
                provider,
                generation=generation + 1,
                child_index=child_index,
                model=model,
                reasoning=reasoning,
            )
            next_population.append(InstructionGenome(candidate=child))
            child_index += 1
        population = _normalize_population(next_population)

    if best_result is None:
        raise RuntimeError("INSPO evolution did not evaluate any prompt")
    return InspoEvolutionResult(
        best=best_result,
        population=_normalize_population(population),
        replay_buffer=replay,
        all_results=all_results,
        guidelines=all_guidelines,
    )
