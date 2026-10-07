import { useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { useLabelOrderSet, useRunQueue, type QueueItem } from "@/api";
import { ReviewItem, type Verdict } from "@/components/ReviewItem";

interface ReviewProps {
  name: string;
}

const keyOf = (item: QueueItem) => `${item.fixture.id}|${item.orders.join("|")}`;

const Review: React.FC<ReviewProps> = ({ name }) => {
  const { data: queue } = useRunQueue(name);
  const labelOrderSet = useLabelOrderSet();
  const navigate = useNavigate();
  const [items] = useState(queue.items);
  const [matched] = useState(queue.matched);
  const [index, setIndex] = useState(0);
  const [saved, setSaved] = useState<Record<string, Verdict>>({});
  const [error, setError] = useState<string | null>(null);

  if (items.length === 0) {
    return <Navigate to={`/runs/${name}`} replace />;
  }

  const item = items[index];

  const advance = () => {
    if (index + 1 >= items.length) {
      navigate(`/runs/${name}`);
    } else {
      setIndex(index + 1);
    }
  };

  const save = async (verdict: Verdict) => {
    setError(null);
    try {
      await labelOrderSet.mutateAsync({ fixtureId: item.fixture.id, orders: item.orders, ...verdict });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return;
    }
    setSaved({ ...saved, [keyOf(item)]: verdict });
    advance();
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-baseline gap-6 border-b px-6 py-3 text-sm">
        <Link to={`/runs/${name}`} className="text-muted-foreground hover:underline">
          Back to run
        </Link>
        <span className="font-medium">
          {index + 1} of {items.length} to review
        </span>
        <span className="text-muted-foreground">{matched} matched existing labels</span>
        {error && <span className="text-destructive">{error}</span>}
      </div>
      <ReviewItem
        key={keyOf(item)}
        item={item}
        saved={saved[keyOf(item)]}
        pending={labelOrderSet.isPending}
        canGoBack={index > 0}
        onSave={save}
        onSkip={advance}
        onBack={() => setIndex(index - 1)}
      />
    </div>
  );
};

export const ReviewScreen: React.FC = () => {
  const { runName } = useParams();
  return runName ? <Review key={runName} name={runName} /> : null;
};
