import type { PropsWithChildren } from "react";

interface CardProps {
  title: string;
}

export function Card({ title, children }: PropsWithChildren<CardProps>) {
  return (
    <section
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: "1.25rem",
        marginBottom: "1.25rem",
        background: "#fff",
      }}
    >
      <h2 style={{ fontSize: "1rem", marginTop: 0, marginBottom: "0.75rem" }}>{title}</h2>
      {children}
    </section>
  );
}
