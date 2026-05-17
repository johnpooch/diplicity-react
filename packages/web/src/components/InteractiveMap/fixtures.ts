export const TOY_DSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400">
  <defs><style>.label{font-family:serif}</style></defs>
  <g id="background"><rect width="600" height="400" fill="#cce"/></g>
  <g id="provinces" style="display:none">
    <path id="alpha" d="M105 70 L210 65 L235 130 L200 200 L110 205 L90 135 Z"/>
    <path id="beta" d="M250 235 L360 230 L385 295 L350 365 L255 370 L230 300 Z"/>
    <path id="gamma" d="M395 70 L510 65 L535 130 L500 200 L405 205 L375 135 Z"/>
  </g>
  <g id="named-coasts" style="display:none">
    <path id="alpha/nc" d="M230 95 L280 90 L275 140 Z"/>
  </g>
  <g id="unit-positions" style="display:none">
    <circle id="alpha" cx="150" cy="130"/>
    <circle id="beta" cx="300" cy="300"/>
    <circle id="gamma" cx="450" cy="130"/>
    <circle id="alpha/nc" cx="210" cy="110"/>
  </g>
  <g id="supply-centers" style="display:none">
    <circle id="alpha" cx="110" cy="175"/>
    <circle id="gamma" cx="490" cy="175"/>
  </g>
  <g id="province-names"><text x="135" y="100">A</text></g>
  <g id="borders"><path d="M305 65 L305 225 L255 365" fill="none" stroke="#6b6b80" stroke-width="2"/></g>
  <g id="foreground"><circle cx="300" cy="200" r="3"/></g>
</svg>`;

export const CONVOY_DSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 360">
  <g id="background"><rect width="600" height="360" fill="#cce"/></g>
  <g id="provinces" style="display:none">
    <path id="alpha" d="M60 60 L190 65 L185 185 L65 180 Z"/>
    <path id="beta" d="M235 220 L370 225 L365 335 L240 330 Z"/>
    <path id="gamma" d="M415 60 L545 65 L540 185 L420 180 Z"/>
  </g>
  <g id="unit-positions" style="display:none">
    <circle id="alpha" cx="120" cy="120"/>
    <circle id="beta" cx="300" cy="280"/>
    <circle id="gamma" cx="480" cy="120"/>
  </g>
</svg>`;
