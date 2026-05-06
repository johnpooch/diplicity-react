import React from "react";
import { Link } from "react-router";
import { GuideContent } from "@/components/GuideContent";

const LearnToPlayPublic: React.FC = () => (
  <div className="w-full bg-background">
    {/* Solid top bar */}
    <header className="sticky top-0 z-50 bg-background border-b border-border flex items-center justify-between px-6 lg:px-[6vw] py-4">
      <Link
        to="/"
        className="flex items-center gap-3 font-semibold text-[18px] text-foreground no-underline"
      >
        <div className="size-8 rounded-full bg-secondary overflow-hidden shrink-0">
          <img
            src="/otto.png"
            alt="Diplicity"
            className="w-full h-full object-cover"
          />
        </div>
        <span>Diplicity</span>
      </Link>
      <div className="flex items-center gap-2">
        <Link
          to="/"
          className="inline-flex items-center justify-center h-9 px-4 text-sm font-medium border border-border text-foreground rounded-md hover:bg-secondary transition-colors"
        >
          Sign in
        </Link>
        <Link
          to="/register"
          className="inline-flex items-center justify-center h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Register
        </Link>
      </div>
    </header>

    {/* Masthead */}
    <header className="text-center px-6 pt-24 pb-14 border-b border-border">
      <div className="text-xs tracking-[0.18em] uppercase text-muted-foreground mb-[18px]">
        Quick-start guide
      </div>
      <h1 className="text-[clamp(36px,4.5vw,56px)] font-semibold tracking-[-0.01em] leading-[1.1] max-w-[16ch] mx-auto mb-6">
        Learn the rules in five minutes.
      </h1>
      <p className="text-[18px] leading-[1.6] text-muted-foreground max-w-[600px] mx-auto mb-7">
        Diplomacy looks like a war game. It isn&apos;t — at least not in the
        usual sense. The board is a stage; the real game is the conversation
        around it.
      </p>
      <div className="inline-flex gap-[18px] text-xs tracking-[0.14em] uppercase text-muted-foreground border-t border-b border-border py-3 px-5">
        <span>≈ 5 min read</span>
        <span>·</span>
        <span>12 sections</span>
        <span>·</span>
        <span>No prior experience</span>
      </div>
    </header>

    {/* Guide content */}
    <GuideContent />

    {/* End CTA */}
    <section className="text-center py-24 px-6 border-t border-border bg-secondary">
      <div className="text-xs tracking-[0.18em] uppercase text-muted-foreground mb-4">
        Now, the hard part
      </div>
      <h2 className="text-[clamp(28px,3.5vw,40px)] font-semibold tracking-[-0.01em] leading-[1.15] max-w-[18ch] mx-auto mb-7">
        Find seven players. Or seven enemies. Same thing.
      </h2>
      <Link
        to="/"
        className="inline-flex items-center justify-center h-11 px-6 text-[15px] font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
      >
        Sign in to play
      </Link>
    </section>

    {/* Footer */}
    <footer className="py-8 px-6 border-t border-border text-center text-sm text-muted-foreground">
      <div>Diplicity · 2014–2026</div>
      <div className="mt-2 flex justify-center gap-5">
        <a
          href="https://diplicity.notion.site/Diplicity-FAQ-7b4e0a119eb54c69b80b411f14d43bb9"
          target="_blank"
          rel="noreferrer"
          className="hover:text-foreground transition-colors"
        >
          FAQ
        </a>
        <a
          href="https://github.com/johnpooch/diplicity-react"
          target="_blank"
          rel="noreferrer"
          className="hover:text-foreground transition-colors"
        >
          GitHub
        </a>
      </div>
    </footer>
  </div>
);

export { LearnToPlayPublic };
