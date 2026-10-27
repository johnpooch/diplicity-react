import React from "react";
import Markdown from "react-markdown";
import codeOfConduct from "./codeOfConduct.md?raw";

const CodeOfConduct: React.FC = () => (
  <article className="prose prose-neutral dark:prose-invert max-w-none">
    <Markdown>{codeOfConduct}</Markdown>
  </article>
);

export { CodeOfConduct };
