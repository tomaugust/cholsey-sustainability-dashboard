/** Flesch reading ease (higher is easier; 60+ is plain English). */
function syllables(word: string): number {
  const w = word.toLowerCase().replace(/[^a-z]/g, "");
  if (w.length <= 3) return w ? 1 : 0;
  const groups = w
    .replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, "")
    .replace(/^y/, "")
    .match(/[aeiouy]{1,2}/g);
  return Math.max(groups?.length ?? 1, 1);
}

export function fleschReadingEase(text: string): number {
  const sentences =
    text.split(/[.!?]+(?:\s|$)/).filter((s) => s.trim()).length || 1;
  const words = text.split(/\s+/).filter((w) => /[a-z]/i.test(w));
  if (words.length === 0) return 100;
  const syl = words.reduce((n, w) => n + syllables(w), 0);
  return (
    206.835 - 1.015 * (words.length / sentences) - 84.6 * (syl / words.length)
  );
}
