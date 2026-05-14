import type { DecorativeElement } from "@/types/variant";

interface DecorativeLayerProps {
  elements: DecorativeElement[];
  hiddenIds?: Set<string>;
}

export function DecorativeLayer({ elements, hiddenIds }: DecorativeLayerProps) {
  return (
    <>
      {elements.map((el) => (
        <DecorativeGroup key={el.id} element={el} hiddenIds={hiddenIds} />
      ))}
    </>
  );
}

interface DecorativeGroupProps {
  element: DecorativeElement;
  hiddenIds?: Set<string>;
}

function DecorativeGroup({ element, hiddenIds }: DecorativeGroupProps) {
  if (hiddenIds?.has(element.id)) return null;
  const children = element.children ?? [];
  return (
    <g>
      {element.content && (
        <g dangerouslySetInnerHTML={{ __html: element.content }} />
      )}
      {children.map((child) => (
        <DecorativeGroup key={child.id} element={child} hiddenIds={hiddenIds} />
      ))}
    </g>
  );
}
