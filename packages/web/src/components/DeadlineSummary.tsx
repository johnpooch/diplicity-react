import React from "react";

interface DeadlineSummaryProps {
  movementPhaseDuration: string | null;
  retreatPhaseDuration?: string | null;
}

export const DeadlineSummary: React.FC<DeadlineSummaryProps> = ({
  movementPhaseDuration,
  retreatPhaseDuration,
}) => {
  if (!movementPhaseDuration) {
    return <span>No automatic deadlines (sandbox)</span>;
  }

  if (!retreatPhaseDuration || retreatPhaseDuration === movementPhaseDuration) {
    return <span>Phases resolve every {movementPhaseDuration}</span>;
  }

  return (
    <span>
      Movement: {movementPhaseDuration}, Retreat/Adjustment:{" "}
      {retreatPhaseDuration}
    </span>
  );
};
