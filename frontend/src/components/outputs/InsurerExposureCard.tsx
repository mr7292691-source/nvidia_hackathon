import type { InsurerExposureReport } from "../../types/decision";
import { Card } from "../common/Card";
import { StatusBadge } from "../common/StatusBadge";

interface InsurerExposureCardProps {
  report: InsurerExposureReport | null;
}

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function InsurerExposureCard({ report }: InsurerExposureCardProps) {
  if (!report) {
    return <Card title="Insurer Exposure">No exposure computed yet.</Card>;
  }

  return (
    <Card title="Insurer Exposure">
      <div style={{ marginBottom: "0.75rem" }}>
        <StatusBadge status={report.approved ? "pass" : "pending"} label={report.approved ? "Approved" : "Awaiting approval"} />
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #eee" }}>
            <th>Policy</th>
            <th>TIV</th>
            <th>Limit</th>
            <th>Deductible</th>
            <th>Est. Exposure</th>
          </tr>
        </thead>
        <tbody>
          {report.policies.map((p) => (
            <tr key={p.policy_id} style={{ borderBottom: "1px solid #f2f2f2" }}>
              <td>{p.policy_id}</td>
              <td>{currency.format(p.tiv_usd)}</td>
              <td>{currency.format(p.limit_usd)}</td>
              <td>{currency.format(p.deductible_usd)}</td>
              <td>{currency.format(p.estimated_exposure_usd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ fontWeight: 600 }}>Total: {currency.format(report.total_estimated_exposure_usd)}</p>
      <p style={{ fontSize: "0.8rem", color: "#999" }}>
        Evidence ref: {report.evidence_ref} — deterministic TIV/limit/deductible math, not LLM-generated.
      </p>
    </Card>
  );
}
