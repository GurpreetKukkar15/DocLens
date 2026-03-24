import { Lightbulb } from "lucide-react";

function ThemePanel({ themes }) {
  const themeBlocks = themes.split(/THEME \d+ -/).filter(t => t.trim());

  return (
    <div className="theme-container">
      <h2>
        <Lightbulb size={20} />
        Identified Themes
      </h2>

      {themeBlocks.length === 0 ? (
        <p className="no-themes">No common themes identified for this query.</p>
      ) : (
        <div className="theme-blocks">
          {themeBlocks.map((block, i) => {
            const lines = block.trim().split("\n").filter(l => l.trim());
            const title = lines[0];
            const body = lines.slice(1).join("\n");

            return (
              <div key={i} className="theme-card">
                <div className="theme-title">
                  Theme {i + 1} — {title}
                </div>
                <div className="theme-body">
                  {body.split("\n").map((line, j) => (
                    <p key={j}>{line}</p>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ThemePanel;