import React, { Suspense } from "react";
import { Link } from "react-router";
import { Newspaper } from "lucide-react";

import { ScreenContainer } from "@/components/ui/screen-container";
import { Skeleton } from "@/components/ui/skeleton";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Notice } from "@/components/Notice";
import { useBlogListSuspense } from "@/api/generated/endpoints";

const BlogList: React.FC = () => {
  const { data: posts } = useBlogListSuspense();

  if (posts.length === 0) {
    return (
      <Notice
        title="No posts yet"
        message="Check back soon."
        icon={Newspaper}
      />
    );
  }

  return (
    <div className="space-y-3">
      {posts.map(post => (
        <Link
          key={post.slug}
          to={`/blog/${post.slug}`}
          className="block rounded-lg border p-4 transition-colors hover:bg-accent"
        >
          <article className="space-y-1">
            <h2 className="text-lg font-semibold">{post.title}</h2>
            <p className="text-xs text-muted-foreground">
              <time dateTime={post.createdAt}>
                {new Date(post.createdAt).toLocaleDateString(undefined, {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </time>
            </p>
            <p className="text-sm text-muted-foreground">{post.summary}</p>
          </article>
        </Link>
      ))}
    </div>
  );
};

const BlogListSkeleton: React.FC = () => (
  <div className="space-y-3">
    {Array.from({ length: 3 }, (_, index) => (
      <div key={index} className="space-y-2 rounded-lg border p-4">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-4 w-full" />
      </div>
    ))}
  </div>
);

const BlogListSuspense: React.FC = () => (
  <ScreenContainer>
    <h1 className="text-2xl font-bold">Blog</h1>
    <QueryErrorBoundary>
      <Suspense fallback={<BlogListSkeleton />}>
        <BlogList />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { BlogListSuspense as BlogList };
