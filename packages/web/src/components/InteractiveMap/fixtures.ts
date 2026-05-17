export const TOY_DSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
  <defs><style>.label{font-family:serif}</style></defs>
  <g id="background"><rect width="200" height="100" fill="#cce"/></g>
  <g id="provinces" style="display:none">
    <path id="alpha" d="M0 0 L10 0 L10 10 Z"/>
    <path id="beta" d="M20 0 L30 0 L30 10 Z"/>
    <path id="gamma" d="M40 0 L50 0 L50 10 Z"/>
  </g>
  <g id="named-coasts" style="display:none">
    <path id="alpha/nc" d="M0 0 L5 0 L5 5 Z"/>
  </g>
  <g id="unit-positions" style="display:none">
    <circle id="alpha" cx="5" cy="5"/>
    <circle id="beta" cx="25" cy="5"/>
    <circle id="gamma" cx="45" cy="5"/>
    <circle id="alpha/nc" cx="2" cy="3"/>
  </g>
  <g id="supply-centers" style="display:none">
    <circle id="alpha" cx="5" cy="8"/>
    <circle id="gamma" cx="45" cy="8"/>
  </g>
  <g id="province-names"><text x="5" y="9">A</text></g>
  <g id="borders"><path d="M10 0 L10 10"/></g>
  <g id="foreground"><circle cx="100" cy="50" r="2"/></g>
</svg>`;

export const CONVOY_DSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 90">
  <g id="background"><rect width="120" height="90" fill="#cce"/></g>
  <g id="provinces" style="display:none">
    <path id="alpha" d="M10 10 L30 10 L30 30 Z"/>
    <path id="beta" d="M50 60 L70 60 L70 80 Z"/>
    <path id="gamma" d="M90 10 L110 10 L110 30 Z"/>
  </g>
  <g id="unit-positions" style="display:none">
    <circle id="alpha" cx="20" cy="20"/>
    <circle id="beta" cx="60" cy="70"/>
    <circle id="gamma" cx="100" cy="20"/>
  </g>
</svg>`;
