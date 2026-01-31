import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Province, Nation } from "@/types/variant";
import { validateProvinceId } from "@/utils/idSuggestion";

interface ProvinceTableProps {
  provinces: Province[];
  nations: Nation[];
  selectedProvinceId: string | null;
  onProvinceSelect: (provinceId: string) => void;
  onProvinceHover: (provinceId: string | null) => void;
  onProvinceUpdate: (
    provinceId: string,
    updates: Partial<Pick<Province, "id" | "name" | "type" | "homeNation" | "supplyCenter" | "startingUnit">>
  ) => void;
  validationErrors: Map<string, string[]>;
}

const PROVINCE_TYPES: Province["type"][] = ["land", "sea", "coastal", "namedCoasts"];

export const ProvinceTable: React.FC<ProvinceTableProps> = ({
  provinces,
  nations,
  selectedProvinceId,
  onProvinceSelect,
  onProvinceHover,
  onProvinceUpdate,
  validationErrors,
}) => {
  const handleNameChange = (province: Province, newName: string) => {
    onProvinceUpdate(province.id, { name: newName });
  };

  const handleIdChange = (province: Province, newId: string) => {
    onProvinceUpdate(province.id, { id: newId.toLowerCase() });
  };

  const handleTypeChange = (province: Province, newType: Province["type"]) => {
    const updates: Partial<Province> = { type: newType };

    if (newType === "sea" && province.startingUnit?.type === "Army") {
      updates.startingUnit = null;
    }
    if (newType === "land" && province.startingUnit?.type === "Fleet") {
      updates.startingUnit = null;
    }

    onProvinceUpdate(province.id, updates);
  };

  const handleHomeNationChange = (province: Province, nationId: string | null) => {
    const updates: Partial<Province> = { homeNation: nationId };

    if (!nationId && province.startingUnit) {
      updates.startingUnit = null;
    }

    onProvinceUpdate(province.id, updates);
  };

  const handleSupplyCenterChange = (province: Province, isSupplyCenter: boolean) => {
    const updates: Partial<Province> = { supplyCenter: isSupplyCenter };

    if (!isSupplyCenter && province.startingUnit) {
      updates.startingUnit = null;
    }

    onProvinceUpdate(province.id, updates);
  };

  const handleStartingUnitChange = (province: Province, unitType: "Army" | "Fleet" | null) => {
    onProvinceUpdate(province.id, {
      startingUnit: unitType ? { type: unitType } : null,
    });
  };

  const getIdValidation = (province: Province): string | null => {
    const validation = validateProvinceId(province.id);
    if (!validation.valid) return validation.error || null;

    const duplicates = provinces.filter((p) => p.id === province.id && p.elementId !== province.elementId);
    if (duplicates.length > 0) {
      return "ID must be unique";
    }

    return null;
  };

  const getAvailableUnitTypes = (province: Province): ("Army" | "Fleet")[] => {
    switch (province.type) {
      case "sea":
        return ["Fleet"];
      case "land":
        return ["Army"];
      case "coastal":
      case "namedCoasts":
        return ["Army", "Fleet"];
      default:
        return [];
    }
  };

  return (
    <div className="overflow-auto max-h-[60vh] border rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-muted sticky top-0">
          <tr>
            <th className="px-3 py-2 text-left font-medium">ID</th>
            <th className="px-3 py-2 text-left font-medium">Name</th>
            <th className="px-3 py-2 text-left font-medium">Type</th>
            <th className="px-3 py-2 text-left font-medium">Home Nation</th>
            <th className="px-3 py-2 text-center font-medium">SC</th>
            <th className="px-3 py-2 text-left font-medium">Starting Unit</th>
          </tr>
        </thead>
        <tbody>
          {provinces.map((province) => {
            const isSelected = province.id === selectedProvinceId;
            const idError = getIdValidation(province);
            const errors = validationErrors.get(province.id) || [];
            const availableUnitTypes = getAvailableUnitTypes(province);
            const canHaveStartingUnit =
              province.homeNation && province.supplyCenter && availableUnitTypes.length > 0;

            return (
              <tr
                key={province.elementId}
                className={`border-t cursor-pointer hover:bg-muted/50 ${
                  isSelected ? "bg-yellow-100" : ""
                }`}
                onClick={() => onProvinceSelect(province.id)}
                onMouseEnter={() => onProvinceHover(province.id)}
                onMouseLeave={() => onProvinceHover(null)}
              >
                <td className="px-3 py-2">
                  <div className="space-y-1">
                    <Input
                      value={province.id}
                      onChange={(e) => handleIdChange(province, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className={`w-16 font-mono ${idError ? "border-destructive" : ""}`}
                      maxLength={3}
                    />
                    {idError && (
                      <p className="text-xs text-destructive">{idError}</p>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <Input
                    value={province.name}
                    onChange={(e) => handleNameChange(province, e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    placeholder="Province name"
                    className="min-w-32"
                  />
                </td>
                <td className="px-3 py-2">
                  <Select
                    value={province.type}
                    onValueChange={(value) =>
                      handleTypeChange(province, value as Province["type"])
                    }
                  >
                    <SelectTrigger
                      className="w-32"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PROVINCE_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                <td className="px-3 py-2">
                  <Select
                    value={province.homeNation || "none"}
                    onValueChange={(value) =>
                      handleHomeNationChange(province, value === "none" ? null : value)
                    }
                  >
                    <SelectTrigger
                      className="w-32"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <SelectValue placeholder="None" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {nations.map((nation) => (
                        <SelectItem key={nation.id} value={nation.id}>
                          <span className="flex items-center gap-2">
                            <span
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: nation.color }}
                            />
                            {nation.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                <td className="px-3 py-2 text-center">
                  <Checkbox
                    checked={province.supplyCenter}
                    onCheckedChange={(checked) =>
                      handleSupplyCenterChange(province, checked === true)
                    }
                    onClick={(e) => e.stopPropagation()}
                  />
                </td>
                <td className="px-3 py-2">
                  <Select
                    value={province.startingUnit?.type || "none"}
                    onValueChange={(value) =>
                      handleStartingUnitChange(
                        province,
                        value === "none" ? null : (value as "Army" | "Fleet")
                      )
                    }
                    disabled={!canHaveStartingUnit}
                  >
                    <SelectTrigger
                      className="w-24"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <SelectValue placeholder="None" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {availableUnitTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.length > 0 && (
                    <div className="mt-1">
                      {errors.map((error, i) => (
                        <p key={i} className="text-xs text-destructive">
                          {error}
                        </p>
                      ))}
                    </div>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
