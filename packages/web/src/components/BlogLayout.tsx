import React from "react";
import { Link } from "react-router";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { SafeAreaView } from "@/components/SafeAreaView";

interface BlogLayoutProps {
  children: React.ReactNode;
}

const BlogLayout: React.FC<BlogLayoutProps> = ({ children }) => (
  <SafeAreaView className="min-h-dvh w-full">
    <header className="border-b">
      <div className="mx-auto max-w-[672px] px-4 py-3">
        <Link to="/blog" className="inline-flex items-center gap-3">
          <DiplicityLogo />
          <span className="font-semibold">Diplicity</span>
        </Link>
      </div>
    </header>
    <main className="mx-auto max-w-[672px] px-4 py-6">{children}</main>
  </SafeAreaView>
);

export { BlogLayout };
