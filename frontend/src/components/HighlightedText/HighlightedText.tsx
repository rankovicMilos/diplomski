import cn from "@/src/utils/cn";

type HighlightedTextProps = {
  text: string,
  highlightText?: string | undefined,
  className?: string
}

const HighlightedText = ({ text, highlightText, className }: HighlightedTextProps) => {
  if (!highlightText?.trim()) {
    return <span>{text}</span>;
  }

  const escapedQuery = highlightText.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  const parts = text.split(new RegExp(`(${escapedQuery})`, "gi"));

  return (
    <span>
      {parts.map((part, index) => {
        const isMatch = part.toLowerCase() === highlightText.toLowerCase();
        return isMatch ? (
          <mark
            key={`${index}-${part.slice(0, 10)}`}
            className={cn("bg-yellow-300 text-yellow-900 rounded", className)}
          >
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        );
      })}
    </span>
  );
}

export default HighlightedText;