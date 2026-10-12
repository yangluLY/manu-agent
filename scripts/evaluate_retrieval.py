import json
import sys
from dataclasses import dataclass
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.retrieval.retriever import KnowledgeRetriever
from services.database.session import SessionLocal

CASES_FILE = Path("tests/knowledge/evaluation_cases.json")
TOP_K = 5

# 第一轮建议从一组候选阈值中扫描，
# 不要直接认定某个固定值一定最优。
THRESHOLDS = [
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
]


@dataclass
class EvaluationSummary:
    threshold: float
    positive_cases: int
    positive_hits: int
    top1_hits: int
    reciprocal_rank_sum: float
    negative_cases: int
    negative_rejections: int

    @property
    def hit_at_k(self) -> float:
        if self.positive_cases == 0:
            return 0.0
        return self.positive_hits / self.positive_cases

    @property
    def top1_accuracy(self) -> float:
        if self.positive_cases == 0:
            return 0.0
        return self.top1_hits / self.positive_cases

    @property
    def mrr(self) -> float:
        if self.positive_cases == 0:
            return 0.0
        return self.reciprocal_rank_sum / self.positive_cases

    @property
    def negative_rejection_rate(self) -> float:
        if self.negative_cases == 0:
            return 0.0
        return self.negative_rejections / self.negative_cases

    @property
    def balanced_score(self) -> float:
        """
        简单用于比较阈值的综合指标：
        正样本 Hit@K 与负样本拒绝率取平均。

        不是通用行业标准，只用于本项目第一版调参。
        """
        return (
            self.hit_at_k
            + self.negative_rejection_rate
        ) / 2


def load_cases() -> list[dict]:
    if not CASES_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation cases not found: {CASES_FILE}"
        )

    return json.loads(
        CASES_FILE.read_text(encoding="utf-8")
    )


def evaluate_threshold(
    retriever: KnowledgeRetriever,
    cases: list[dict],
    threshold: float,
    verbose: bool = False,
) -> EvaluationSummary:

    positive_cases = 0
    positive_hits = 0
    top1_hits = 0
    reciprocal_rank_sum = 0.0

    negative_cases = 0
    negative_rejections = 0

    for case in cases:
        query = case["query"]
        should_retrieve = case["should_retrieve"]
        expected_documents = set(
            case.get("expected_documents", [])
        )

        results = retriever.search(
            query=query,
            top_k=TOP_K,
            min_score=threshold,
        )

        returned_documents = [
            result.document_name
            for result in results
        ]

        if should_retrieve:
            positive_cases += 1

            matched_rank = None

            for rank, result in enumerate(
                results,
                start=1,
            ):
                if result.document_name in expected_documents:
                    matched_rank = rank
                    break

            if matched_rank is not None:
                positive_hits += 1
                reciprocal_rank_sum += 1.0 / matched_rank

                if matched_rank == 1:
                    top1_hits += 1

            if verbose:
                print()
                print(
                    "[POSITIVE]",
                    case["id"],
                    "PASS" if matched_rank else "FAIL",
                )
                print("Query:", query)
                print(
                    "Expected:",
                    sorted(expected_documents),
                )
                print(
                    "Returned:",
                    returned_documents,
                )

                for result in results:
                    print(
                        f"  {result.score:.4f}"
                        f" | {result.document_name}"
                        f" | chunk={result.chunk_index}"
                    )

        else:
            negative_cases += 1

            if len(results) == 0:
                negative_rejections += 1
                passed = True
            else:
                passed = False

            if verbose:
                print()
                print(
                    "[NEGATIVE]",
                    case["id"],
                    "PASS" if passed else "FAIL",
                )
                print("Query:", query)
                print(
                    "Returned:",
                    returned_documents,
                )

                for result in results:
                    print(
                        f"  {result.score:.4f}"
                        f" | {result.document_name}"
                        f" | chunk={result.chunk_index}"
                    )

    return EvaluationSummary(
        threshold=threshold,
        positive_cases=positive_cases,
        positive_hits=positive_hits,
        top1_hits=top1_hits,
        reciprocal_rank_sum=reciprocal_rank_sum,
        negative_cases=negative_cases,
        negative_rejections=negative_rejections,
    )


def print_summary(
    summary: EvaluationSummary,
) -> None:

    print(
        f"{summary.threshold:<10.2f}"
        f"{summary.hit_at_k:<12.2%}"
        f"{summary.top1_accuracy:<12.2%}"
        f"{summary.mrr:<10.4f}"
        f"{summary.negative_rejection_rate:<18.2%}"
        f"{summary.balanced_score:<10.4f}"
    )


def main():
    cases = load_cases()

    db = SessionLocal()

    try:
        retriever = KnowledgeRetriever(
            db=db,
        )

        print("=" * 80)
        print("ManuAgent Retrieval Evaluation")
        print("=" * 80)
        print(f"Cases: {len(cases)}")
        print(f"Top K: {TOP_K}")
        print()

        print(
            f"{'Threshold':<10}"
            f"{'Hit@5':<12}"
            f"{'Top1':<12}"
            f"{'MRR':<10}"
            f"{'Neg Reject':<18}"
            f"{'Balanced':<10}"
        )
        print("-" * 80)

        summaries: list[EvaluationSummary] = []

        for threshold in THRESHOLDS:
            summary = evaluate_threshold(
                retriever=retriever,
                cases=cases,
                threshold=threshold,
                verbose=False,
            )

            summaries.append(summary)
            print_summary(summary)

        best = max(
            summaries,
            key=lambda item: (
                item.balanced_score,
                item.hit_at_k,
                item.mrr,
            ),
        )

        print()
        print("=" * 80)
        print("Best candidate threshold")
        print("=" * 80)

        print(
            f"Threshold: {best.threshold:.2f}"
        )
        print(
            f"Hit@{TOP_K}: {best.hit_at_k:.2%}"
        )
        print(
            f"Top1 Accuracy: "
            f"{best.top1_accuracy:.2%}"
        )
        print(
            f"MRR: {best.mrr:.4f}"
        )
        print(
            f"Negative Rejection: "
            f"{best.negative_rejection_rate:.2%}"
        )
        print(
            f"Balanced Score: "
            f"{best.balanced_score:.4f}"
        )

        print()
        print("=" * 80)
        print(
            "Detailed failures at best threshold"
        )
        print("=" * 80)

        evaluate_threshold(
            retriever=retriever,
            cases=cases,
            threshold=best.threshold,
            verbose=True,
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
