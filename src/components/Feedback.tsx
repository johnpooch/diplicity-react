import React from "react";
import { Snackbar, Alert } from "@mui/material";
import { connect } from "react-redux";
import { actions, selectFeedback } from "../common";

const FeedbackComponent: React.FC<
  ReturnType<typeof selectFeedback> & {
    onClose: () => void;
  }
> = (props) => {
  return (
    <Snackbar
      open={Boolean(props.message)}
      autoHideDuration={3000}
      onClose={props.onClose}
    >
      <Alert
        onClose={props.onClose}
        severity={props.severity}
        variant="filled"
        title={props.message}
      >
        {props.message}
      </Alert>
    </Snackbar>
  );
};

const ConnectedFeedbackComponent = connect(selectFeedback, {
  onClose: actions.clearFeedback,
})(FeedbackComponent);

export default ConnectedFeedbackComponent;
