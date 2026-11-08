(function (root) {
  "use strict";
  const width = 720, height = 520, speed = 115, interactionRadius = 47;
  const start = {x: 357, y: 380};
  const bounds = {left: 66, right: 653, top: 188, bottom: 455};
  const relays = [
    {id: "rihtim", name: "Rıhtım", x: 137, y: 356},
    {id: "ambar", name: "Eski Ambar", x: 343, y: 220},
    {id: "iskele", name: "İskele", x: 592, y: 385}
  ];
  function destination(x, y) {
    return {x: Math.min(bounds.right, Math.max(bounds.left, x)), y: Math.min(bounds.bottom, Math.max(bounds.top, y))};
  }
  function advance(actor, seconds) {
    const dx = actor.target.x - actor.x, dy = actor.target.y - actor.y;
    const length = Math.hypot(dx, dy);
    if (!length) return;
    const fraction = Math.min(1, speed * Math.max(0, seconds) / length);
    actor.x += dx * fraction;
    actor.y += dy * fraction;
  }
  function nearest(actor, completed) {
    return relays.filter(r => !completed.includes(r.id) && Math.hypot(actor.x-r.x, actor.y-r.y) <= interactionRadius)
      .sort((a,b) => Math.hypot(actor.x-a.x,actor.y-a.y) - Math.hypot(actor.x-b.x,actor.y-b.y))[0];
  }
  const world = {width, height, start, bounds, relays, destination, advance, nearest, speed};
  if (typeof module !== "undefined" && module.exports) module.exports = world;
  else root.World = world;
})(typeof window === "undefined" ? global : window);
