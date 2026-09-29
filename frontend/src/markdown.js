// Markdown-lite renderer. Escapes HTML first, so the output is safe to
// inject with dangerouslySetInnerHTML. Supports **bold**, `code`,
// bullet lists, numbered lists, and # headings.

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function inline(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(
      /`([^`]+)`/g,
      '<code class="rounded bg-slate-800 px-1 py-0.5 text-[13px] text-amber-200">$1</code>'
    );
}

export function renderMarkdownLite(raw) {
  const lines = escapeHtml(raw || "").split("\n");
  const html = [];
  let list = null; // "ul" | "ol" | null

  const closeList = () => {
    if (list) {
      html.push(`</${list}>`);
      list = null;
    }
  };

  for (const line of lines) {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    const heading = line.match(/^\s*#{1,4}\s+(.*)$/);

    if (bullet) {
      if (list !== "ul") {
        closeList();
        html.push('<ul class="ml-5 list-disc space-y-1">');
        list = "ul";
      }
      html.push(`<li>${inline(bullet[1])}</li>`);
    } else if (numbered) {
      if (list !== "ol") {
        closeList();
        html.push('<ol class="ml-5 list-decimal space-y-1">');
        list = "ol";
      }
      html.push(`<li>${inline(numbered[1])}</li>`);
    } else if (heading) {
      closeList();
      html.push(`<p class="mt-2 font-semibold text-slate-100">${inline(heading[1])}</p>`);
    } else if (line.trim() === "") {
      closeList();
      html.push('<div class="h-2"></div>');
    } else {
      closeList();
      html.push(`<p>${inline(line)}</p>`);
    }
  }
  closeList();
  return html.join("");
}
