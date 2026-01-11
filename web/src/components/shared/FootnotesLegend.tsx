import "./FootnotesLegend.css";

interface FootnotesLegendProps {
  footnotes: Record<string, string>;
  className?: string;
}

export function FootnotesLegend({ footnotes, className = "" }: FootnotesLegendProps) {
  const entries = Object.entries(footnotes);
  if (entries.length === 0) return null;
  
  return (
    <div className={`footnotes-legend ${className}`}>
      {entries.map(([symbol, text]) => (
        <div key={symbol} className="footnotes-legend__item">
          <span className="footnotes-legend__symbol">{symbol}</span>
          <span className="footnotes-legend__text">{text}</span>
        </div>
      ))}
    </div>
  );
}
