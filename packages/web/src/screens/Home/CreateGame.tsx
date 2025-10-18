import React, { useState, useEffect } from "react";
import { Divider } from "@mui/material";
import { HomeLayout } from "./Layout";
import { useNavigate, useSearchParams } from "react-router";
import { Panel } from "../../components/Panel";
import { Tabs } from "../../components/Tabs";
import { CreateStandardGame } from "./CreateStandardGame";
import { CreateSandboxGame } from "./CreateSandboxGame";
import { useResponsiveness } from "../../components/utils/responsive";

const CreateGame: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const responsiveness = useResponsiveness();
  // Determine initial tab based on query string parameter
  const getInitialTab = (): "standard" | "sandbox" => {
    const sandboxParam = searchParams.get("sandbox");
    if (sandboxParam === "true") {
      return "sandbox";
    }
    return "standard";
  };

  const [currentTab, setCurrentTab] = useState<"standard" | "sandbox">(
    getInitialTab()
  );

  // Update tab when query string changes
  useEffect(() => {
    const newTab = getInitialTab();
    setCurrentTab(newTab);
  }, [searchParams]);

  // Update URL when tab changes
  const handleTabChange = (newTab: "standard" | "sandbox") => {
    setCurrentTab(newTab);
    const newSearchParams = new URLSearchParams(searchParams);
    if (newTab === "sandbox") {
      newSearchParams.set("sandbox", "true");
    } else {
      newSearchParams.delete("sandbox");
    }
    navigate(`?${newSearchParams.toString()}`, { replace: true });
  };

  return (
    <HomeLayout
      content={
        <Panel>
          <Panel.Content>
            <Tabs
              value={currentTab}
              onChange={(_, newValue) =>
                handleTabChange(newValue as "standard" | "sandbox")
              }
              options={[
                { label: "Standard", value: "standard" },
                { label: "Sandbox", value: "sandbox" },
              ]}
            />
            <Divider />
            {currentTab === "standard" && <CreateStandardGame />}
            {currentTab === "sandbox" && <CreateSandboxGame />}
          </Panel.Content>
          {responsiveness.device === "mobile" && (
            <div style={{ height: "56px" }} />
          )}
        </Panel>
      }
    />
  );
};

export { CreateGame };
