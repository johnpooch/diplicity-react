import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { FileQuestion } from "lucide-react";

const NotFound: React.FC = () => {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 items-center px-4 py-10">
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <FileQuestion />
          </EmptyMedia>
          <EmptyTitle>No such prototype</EmptyTitle>
          <EmptyDescription>
            It may have been deleted after the decision it was made for was
            settled.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button asChild>
            <Link to="/">Back to the index</Link>
          </Button>
        </EmptyContent>
      </Empty>
    </div>
  );
};

export { NotFound };
