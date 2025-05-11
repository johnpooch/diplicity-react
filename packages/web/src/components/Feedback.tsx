import React from "react";
import { Snackbar, Alert } from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { feedbackActions, selectFeedback } from "../store";

const Feedback: React.FC = () => {
  const dispatch = useDispatch();
  const feedback = useSelector(selectFeedback);
  const handleClose = () => {
    dispatch(feedbackActions.clearFeedback());
  };
  return (
    <Snackbar
      open={Boolean(feedback.message)}
      autoHideDuration={3000}
      onClose={handleClose}
    >
      <Alert
        onClose={handleClose}
        severity={feedback.severity}
        title={feedback.message}
      >
        {feedback.message}
      </Alert>
    </Snackbar>
  );
};

export { Feedback };
