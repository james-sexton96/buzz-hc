"use client";

import { useEffect, useState } from "react";
import { getScenarios } from "@/lib/api";
import type { Scenario } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Settings } from "lucide-react";

interface QueryFormProps {
  onSubmit: (query: string, tavilyKey: string) => void;
  disabled?: boolean;
}

const TAVILY_KEY_STORAGE = "buzz_hc_tavily_key";

export function QueryForm({ onSubmit, disabled = false }: QueryFormProps) {
  const [query, setQuery] = useState("");
  const [tavilyKey, setTavilyKey] = useState("");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(TAVILY_KEY_STORAGE);
    if (saved) setTavilyKey(saved);
    getScenarios()
      .then(setScenarios)
      .catch(() => {});
  }, []);

  const handleTavilyChange = (val: string) => {
    setTavilyKey(val);
    localStorage.setItem(TAVILY_KEY_STORAGE, val);
  };

  const handleScenario = (value: string | null) => {
    if (!value) return;
    const scenario = scenarios.find((s) => s.label === value);
    if (scenario && scenario.query) setQuery(scenario.query);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSubmit(query.trim(), tavilyKey.trim());
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-medium text-muted-foreground">
              What would you like to research?
            </p>
            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              className="inline-flex items-center justify-center rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="API configuration"
            >
              <Settings size={15} />
            </button>
          </div>

          {scenarios.length > 0 && (
            <div className="space-y-2 mb-5">
              <Label htmlFor="scenario" className="text-xs text-muted-foreground uppercase tracking-wider">
                Scenario preset
              </Label>
              <Select onValueChange={handleScenario} disabled={disabled}>
                <SelectTrigger id="scenario" className="w-full">
                  <SelectValue placeholder="Choose a scenario or write your own…" />
                </SelectTrigger>
                <SelectContent>
                  {scenarios.map((s) => (
                    <SelectItem key={s.label} value={s.label}>
                      <span className="font-medium">{s.label}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Scenario pills */}
              {scenarios.slice(0, 3).map((s) => (
                <button
                  key={s.label}
                  type="button"
                  onClick={() => s.query && setQuery(s.query)}
                  disabled={disabled}
                  className="cursor-pointer bg-primary/8 text-primary border border-primary/20 hover:bg-primary/15 text-[11px] px-2 py-0.5 rounded-full transition-colors mr-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {s.label}
                </button>
              ))}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="query" className="text-xs text-muted-foreground uppercase tracking-wider">
              Research query
            </Label>
            <Textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Projected market size and competitive landscape for GLP-1 agonists in obesity by 2030…"
              disabled={disabled}
              required
              className="resize-none text-sm min-h-[120px] field-sizing-content"
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={disabled || !query.trim()}
          className="w-full rounded-full"
          size="lg"
        >
          {disabled ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              Running pipeline…
            </span>
          ) : (
            "Start Research"
          )}
        </Button>
      </form>

      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>API Configuration</DialogTitle>
            <DialogDescription>
              Your Tavily API key is saved locally in your browser and never sent to our servers.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="tavily-key-dialog" className="text-xs text-muted-foreground uppercase tracking-wider">
              Tavily API key
            </Label>
            <Input
              id="tavily-key-dialog"
              type="password"
              value={tavilyKey}
              onChange={(e) => handleTavilyChange(e.target.value)}
              placeholder="tvly-…"
              className="text-sm"
            />
          </div>
          <DialogFooter>
            <DialogClose>
              <Button variant="outline" size="sm">Done</Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
