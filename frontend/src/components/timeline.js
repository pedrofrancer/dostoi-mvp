// Lista tipo checklist (PRD Seção 27 / TechSpecs Seção 65): "✓" pras
// transições já passadas, "→" pra última (o estado atual).
export function renderTimeline(container, transitions) {
  container.innerHTML = "";
  const ul = document.createElement("ul");
  ul.className = "timeline-list";

  transitions.forEach((transition, index) => {
    const isCurrent = index === transitions.length - 1;
    const li = document.createElement("li");
    li.textContent = `${isCurrent ? "→" : "✓"} ${transition.to}`;
    li.title = `${transition.trigger} — ${new Date(transition.timestamp).toLocaleTimeString()}`;
    if (isCurrent) li.classList.add("timeline-current");
    ul.appendChild(li);
  });

  container.appendChild(ul);
}
