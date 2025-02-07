import { useState } from "react";
import { Box, TextField, Typography, Button } from "@mui/material";
import { parseSvg } from "../common/map/map.parse";

const process = (input: string): string => {
  // Implement your processing logic here
  const parsed = parseSvg(input);
  console.log(parsed);
  return JSON.stringify(parsed, null, 2);
};

const ParseMap = () => {
  const [input, setInput] = useState("");
  const [processedContent, setProcessedContent] = useState("");

  const handleProcess = () => {
    setProcessedContent(process(input));
  };

  const handleCopyToClipboard = () => {
    if (processedContent) {
      navigator.clipboard
        .writeText(processedContent)
        .then(() => {
          console.log("Copied to clipboard");
        })
        .catch((err) => {
          console.error("Failed to copy: ", err);
        });
    }
  };

  return (
    <Box sx={{ padding: 2 }}>
      <TextField
        label="Input"
        multiline
        rows={4}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        fullWidth
      />
      <Button
        variant="contained"
        color="primary"
        onClick={handleProcess}
        sx={{ marginTop: 2 }}
      >
        Process
      </Button>
      <Button
        variant="contained"
        color="secondary"
        onClick={handleCopyToClipboard}
        sx={{ marginTop: 2 }}
      >
        Copy to Clipboard
      </Button>
      {processedContent && (
        <>
          <Typography variant="body1" sx={{ marginTop: 2 }}>
            Processed Content:
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {processedContent}
          </Typography>
        </>
      )}
    </Box>
  );
};
export { ParseMap };
