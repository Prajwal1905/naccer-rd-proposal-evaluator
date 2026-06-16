import ScoreCard from "../components/ScoreCard";
import NoveltySection from "../components/NoveltySection";
import FinancialSection from "../components/FinancialSection";
import FeasibilitySection from "../components/FeasibilitySection";
import MLSection from "../components/MLSection";
import SuggestionsSection from "../components/SuggestionsSection";

export default function ReportPage({ report, onReset }) {
  const final = report.final_report || {};
  const sections = report.proposal_sections || {};

  const recommendationColor =
    {
      RECOMMEND: "bg-green-50 border-green-400 text-green-800",
      "RECOMMEND WITH REVISIONS":
        "bg-yellow-50 border-yellow-400 text-yellow-800",
      "NOT RECOMMENDED": "bg-red-50 border-red-400 text-red-800",
    }[final.overall_recommendation] ||
    "bg-gray-50 border-gray-300 text-gray-700";

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Evaluation Report</h2>
          <p className="text-gray-500 text-sm mt-1">
            {sections.title || "Untitled Proposal"}
          </p>
        </div>
        <button
          onClick={onReset}
          className="text-sm px-4 py-2 border border-gray-300 rounded-lg
                     text-gray-600 hover:bg-gray-100 transition-colors"
        >
          Evaluate Another
        </button>
      </div>

      <div className={`border-l-4 rounded-lg p-5 mb-6 ${recommendationColor}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest mb-1 opacity-70">
              Overall Recommendation
            </p>
            <p className="text-2xl font-bold">{final.overall_recommendation}</p>
          </div>
          <div className="text-right">
            <p className="text-xs font-semibold uppercase tracking-widest mb-1 opacity-70">
              Overall Score
            </p>
            <p className="text-4xl font-bold">
              {final.overall_score}
              <span className="text-lg font-normal">/100</span>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <ScoreCard
          label="Novelty Score"
          value={final.component_scores?.novelty_score}
          max={100}
          invert
        />
        <ScoreCard
          label="Financial Compliance"
          value={final.component_scores?.financial_compliance_score}
          max={100}
        />
        <ScoreCard
          label="Feasibility / Relevance"
          value={final.component_scores?.feasibility_relevance_score}
          max={100}
        />
        <ScoreCard
          label="Approval Probability"
          value={Math.round(
            (final.component_scores?.ml_approval_probability || 0) * 100,
          )}
          max={100}
          suffix="%"
        />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">
          Reviewer Note
        </h3>
        <p className="text-gray-700 leading-relaxed text-sm whitespace-pre-line">
          {final.reviewer_note}
        </p>

        <div className="grid grid-cols-2 gap-6 mt-6">
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">
              Key Strengths
            </p>
            <ul className="space-y-1">
              {(final.key_strengths || []).map((s, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-green-500 font-bold">+</span> {s}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">
              Key Concerns
            </p>
            <ul className="space-y-1">
              {(final.key_concerns || []).map((c, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-red-400 font-bold">-</span> {c}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <NoveltySection data={report.novelty_result} />
        <FinancialSection data={report.financial_result} />
        <FeasibilitySection data={report.feasibility_result} />
        <MLSection data={report.ml_result} />
        <SuggestionsSection data={final.improvement_suggestions} />
      </div>
    </div>
  );
}
