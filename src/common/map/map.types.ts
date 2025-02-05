interface IMapEditor {
    /**
     * Set the owner of a province.
     * @param province The province to set the owner of.
     * @param nation The nation to set as the owner.
     * @returns void
     */
    setOwner: (province: string, nation: string) => void;

    /**
     * Add a unit to a province.
     * @param province The province to add the unit to.
     * @param nation The nation that the unit belongs to.
     * @returns void
     */
    addArmy: (province: string, nation: string) => void;

    /**
     * Add a fleet to a province.
     */
    addFleet: (province: string, nation: string) => void;
}

export type { IMapEditor };