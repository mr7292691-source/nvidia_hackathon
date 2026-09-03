interface StatusBadgeProps {
  status: "pass" | "fail" | "pending" | "unknown";
  label: string;
}

const COLORS: Record<StatusBadgeProps["status"], string> = {
  pass: "#1e8e3e",
  fail: "#c5221f",
  pending: "#e8a300",
  unknown: "#888",
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.4rem",
        padding: "0.15rem 0.6rem",
        borderRadius: 999,
        fontSize: "0.85rem",
        color: "#fff",
        background: COLORS[status],
      }}
    >
      {label}
    </span>
  );
}
