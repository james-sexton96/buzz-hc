"use client";

import Link from "next/link";
import { Search, BarChart2, FileText, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

function HeroPreview() {
  return (
    <div className="bg-card border border-border/50 rounded-2xl shadow-sm p-5 h-full">
      <div className="space-y-3">
        <p className="font-[family-name:var(--font-serif)] text-sm font-semibold leading-snug">
          GLP-1 Agonist Market Access Report 2030
        </p>
        <div className="border-l-2 border-primary/40 pl-2">
          <p className="text-xs text-muted-foreground leading-relaxed">
            The GLP-1 agonist market is projected to exceed $130B by 2030, driven by obesity and T2D approvals…
          </p>
        </div>
        <div className="space-y-1.5 pt-1">
          <div className="bg-muted rounded h-2 w-full" />
          <div className="bg-muted rounded h-2 w-5/6" />
          <div className="bg-muted rounded h-2 w-4/5" />
          <div className="bg-muted rounded h-2 w-full" />
        </div>
        <p className="text-[10px] uppercase tracking-wider text-primary/60 mt-3">
          Competitive Landscape
        </p>
        <div className="space-y-1.5">
          <div className="bg-muted rounded h-2 w-full" />
          <div className="bg-muted rounded h-2 w-3/4" />
          <div className="bg-muted rounded h-2 w-5/6" />
        </div>
        <p className="text-[10px] text-muted-foreground/50 pt-1">
          Sources: FDA, EMA, ClinicalTrials.gov, Bloomberg Health
        </p>
      </div>
    </div>
  );
}

const featureCards = [
  {
    icon: Search,
    title: "Market Access Research",
    description: "Regulatory snapshots, clinical trial summaries, and reimbursement landscape analysis.",
    colSpan: "col-span-1",
  },
  {
    icon: BarChart2,
    title: "Data Analysis",
    description: "Market sizing estimates and competitive landscape mapping from live sources.",
    colSpan: "col-span-1",
  },
  {
    icon: FileText,
    title: "Publication-Ready Reports",
    description: "Structured markdown reports with PDF export, styled for pharma stakeholders.",
    colSpan: "col-span-1",
  },
];

export default function Home() {
  return (
    <div className="space-y-20 py-12">
      {/* Hero */}
      <div className="text-center space-y-6 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-primary/8 text-primary text-xs font-medium px-3 py-1 rounded-full border border-primary/20">
          Multi-agent AI pipeline
        </div>
        <h1 className="text-4xl font-bold tracking-tight">
          Pharma Market Intelligence,{" "}
          <span className="text-primary">in minutes</span>
        </h1>
        <p className="text-muted-foreground text-base leading-relaxed max-w-lg mx-auto">
          A three-agent AI pipeline — Researcher, Analyst, Reporter — that delivers
          structured market access and competitive landscape reports from live data sources.
        </p>
        <div className="flex gap-3 justify-center pt-2">
          <Link
            href="/run"
            className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground px-6 h-10 text-sm font-medium transition-colors hover:bg-primary/90"
          >
            Start Research
          </Link>
          <Link
            href="/sessions"
            className="inline-flex items-center justify-center rounded-full border border-border bg-card px-6 h-10 text-sm font-medium transition-colors hover:bg-muted"
          >
            View History
          </Link>
        </div>
      </div>

      {/* Bento grid */}
      <div className="grid grid-cols-3 gap-4 auto-rows-[minmax(180px,auto)]">
        {/* HeroPreview — spans 2 cols, 2 rows */}
        <motion.div
          className="col-span-2 row-span-2"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0 }}
          whileHover={{ scale: 1.015, y: -2 }}
        >
          <HeroPreview />
        </motion.div>

        {/* Feature 1 */}
        <motion.div
          className="col-span-1"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          whileHover={{ scale: 1.015, y: -2 }}
        >
          <div className="bg-card border border-border/50 rounded-2xl shadow-sm p-5 h-full space-y-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
              <Search className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-sm">{featureCards[0].title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{featureCards[0].description}</p>
          </div>
        </motion.div>

        {/* Feature 2 */}
        <motion.div
          className="col-span-1"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          whileHover={{ scale: 1.015, y: -2 }}
        >
          <div className="bg-card border border-border/50 rounded-2xl shadow-sm p-5 h-full space-y-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
              <BarChart2 className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-sm">{featureCards[1].title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{featureCards[1].description}</p>
          </div>
        </motion.div>

        {/* Feature 3 */}
        <motion.div
          className="col-span-1"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          whileHover={{ scale: 1.015, y: -2 }}
        >
          <div className="bg-card border border-border/50 rounded-2xl shadow-sm p-5 h-full space-y-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-sm">{featureCards[2].title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{featureCards[2].description}</p>
          </div>
        </motion.div>

        {/* CTA card */}
        <motion.div
          className="col-span-2"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25 }}
          whileHover={{ scale: 1.015, y: -2 }}
        >
          <Link href="/run" className="block h-full">
            <div className="bg-gradient-to-br from-primary/8 to-primary/18 border border-primary/20 rounded-2xl shadow-sm p-5 h-full flex items-center justify-between gap-4">
              <div className="space-y-1">
                <p className="font-semibold text-sm">Ready to get started?</p>
                <p className="text-sm text-muted-foreground">Run your first pharma research query in seconds.</p>
              </div>
              <div className="flex items-center gap-2 text-primary font-medium text-sm whitespace-nowrap">
                Start Research
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
