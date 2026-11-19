"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, getDemoUser, setDemoUser } from "@/lib/api";
import type { DemoUser } from "@/lib/types";

export function useDemoUser() {
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [current, setCurrent] = useState<number | null>(null);
  useEffect(() => {
    const fetchUsers = () => api<DemoUser[]>("/demo/users").then(setUsers).catch(() => setUsers([]));
    setCurrent(getDemoUser());
    fetchUsers();
    // Re-fetch too: a just-registered volunteer is not in the list loaded at mount.
    const on = () => {
      setCurrent(getDemoUser());
      fetchUsers();
    };
    window.addEventListener("veravote:user", on);
    return () => window.removeEventListener("veravote:user", on);
  }, []);
  return { users, current, user: users.find((u) => u.id === current) ?? null };
}

const NAV: { href: string; label: string; roles?: string[] }[] = [
  { href: "/", label: "Find a polling unit" },
  { href: "/discrepancies", label: "Discrepancies" },
  { href: "/submit", label: "Submit evidence" },
  { href: "/volunteer", label: "Volunteer", roles: ["volunteer", "citizen"] },
  { href: "/contributor", label: "My assignments", roles: ["volunteer"] },
  { href: "/organisation", label: "Coverage", roles: ["coordinator", "admin"] },
  { href: "/verify", label: "Verification", roles: ["verifier", "senior_reviewer", "admin"] },
  { href: "/about", label: "How it works" },
];

/** The wordmark: an ink mark like the one on a voter's thumbnail, beside the name. */
function Wordmark() {
  return (
    <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight text-ink">
      <svg aria-hidden width="14" height="22" viewBox="0 0 14 22" className="text-violet">
        <path d="M7 1C3.2 1 1 4.6 1 9.5V21h12V9.5C13 4.6 10.8 1 7 1z" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M2.2 9C2.6 5 4.4 2.8 7 2.8S11.4 5 11.8 9c-1.4 1.1-3 1.6-4.8 1.6S3.6 10.1 2.2 9z" fill="currentColor" />
      </svg>
      VeraVote
    </Link>
  );
}

export function Header() {
  const { users, current, user } = useDemoUser();
  const [open, setOpen] = useState(false);
  const path = usePathname();
  const links = NAV.filter((n) => !n.roles || (user && n.roles.includes(user.role)) || (!user && n.href === "/volunteer"));
  const isCurrent = (href: string) => (href === "/" ? path === "/" || path.startsWith("/pu/") : path.startsWith(href));

  return (
    <>
      <div role="note" className="sim-band text-ink text-xs font-bold">
        <p className="mx-auto max-w-5xl px-4 py-1.5">
          <span className="bg-hatch px-1">Demo with simulated data.</span>{" "}
          <span className="bg-hatch px-1 font-normal">VeraVote is independent and is not an INEC platform.</span>
        </p>
      </div>
      <header className="bg-paper">
        <div className="mx-auto max-w-5xl px-4 pt-4 pb-2 flex items-center gap-4">
          <Wordmark />
          <button
            className="ml-auto md:hidden rounded-[3px] border border-ink/30 px-3 py-1.5 text-sm font-bold"
            aria-expanded={open}
            aria-controls="site-nav"
            onClick={() => setOpen(!open)}
          >
            {open ? "Close menu" : "Menu"}
          </button>
          <label className="hidden md:flex ml-auto items-center gap-2 text-sm">
            <span className="text-ink-soft">Viewing as</span>
            <UserSelect users={users} current={current} />
          </label>
        </div>
        <nav id="site-nav" className={`${open ? "block" : "hidden"} md:block border-b-2 border-ink`}>
          <ul className="mx-auto max-w-5xl px-4 flex flex-col md:flex-row md:flex-wrap md:gap-x-6 text-sm">
            {links.map((n) => (
              <li key={n.href}>
                <Link
                  href={n.href}
                  aria-current={isCurrent(n.href) ? "page" : undefined}
                  className="block py-2 border-b-4 border-transparent hover:border-ink/20 aria-[current=page]:border-violet aria-[current=page]:font-bold"
                  onClick={() => setOpen(false)}
                >
                  {n.label}
                </Link>
              </li>
            ))}
            <li className="md:hidden py-3 border-t border-rule">
              <label className="flex flex-col gap-1">
                <span className="text-ink-soft text-xs">Viewing as (demo sign-in)</span>
                <UserSelect users={users} current={current} />
              </label>
            </li>
          </ul>
        </nav>
      </header>
    </>
  );
}

function UserSelect({ users, current }: { users: DemoUser[]; current: number | null }) {
  return (
    <select
      className="rounded-[3px] border border-ink/30 bg-sheet px-2 py-1.5 text-sm max-w-full"
      value={current ?? ""}
      onChange={(e) => setDemoUser(e.target.value ? Number(e.target.value) : null)}
    >
      <option value="">Public visitor (no account)</option>
      {users.map((u) => (
        <option key={u.id} value={u.id}>
          {u.name} ({u.persona})
        </option>
      ))}
    </select>
  );
}
