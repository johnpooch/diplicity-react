import React, { Suspense } from "react";
import { Link } from "react-router";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SearchX } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  QueryErrorBoundary,
  QueryErrorFallback,
} from "@/components/QueryErrorBoundary";
import { Notice } from "@/components/Notice";
import { useBlogRetrieveSuspense } from "@/api/generated/endpoints";
import { useRequiredParams } from "@/hooks";
import { isNotFoundError } from "@/utils/network";

const BlogPost: React.FC = () => {
  const { slug } = useRequiredParams<{ slug: string }>();
  const { data: post } = useBlogRetrieveSuspense(slug);

  return (
    <article className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold">{post.title}</h1>
        <p className="text-sm text-muted-foreground">
          <time dateTime={post.createdAt}>
            {new Date(post.createdAt).toLocaleDateString(undefined, {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </time>
        </p>
        <p className="text-lg text-muted-foreground">{post.summary}</p>
      </header>
      <div className="prose prose-neutral dark:prose-invert max-w-none prose-img:rounded-lg">
        <Markdown remarkPlugins={[remarkGfm]}>{post.body}</Markdown>
      </div>
    </article>
  );
};

const BlogPostSkeleton: React.FC = () => (
  <div className="space-y-6">
    <div className="space-y-2">
      <Skeleton className="h-9 w-3/4" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-6 w-full" />
    </div>
    <div className="space-y-3">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
    </div>
  </div>
);

const renderFallback = (error: Error, onReset: () => void) =>
  isNotFoundError(error) ? (
    <Notice
      icon={SearchX}
      title="Post not found"
      message="It may have been removed or the link may be wrong."
      actions={
        <Button asChild>
          <Link to="/blog">See all posts</Link>
        </Button>
      }
    />
  ) : (
    <QueryErrorFallback error={error} onReset={onReset} />
  );

const BlogPostSuspense: React.FC = () => (
  <QueryErrorBoundary renderFallback={renderFallback}>
    <Suspense fallback={<BlogPostSkeleton />}>
      <BlogPost />
    </Suspense>
  </QueryErrorBoundary>
);

export { BlogPostSuspense as BlogPost };
