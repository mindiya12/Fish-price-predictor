import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="mt-10 border-t border-black/5 bg-white">
      <div className="mx-auto w-full max-w-6xl px-4 py-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="font-[var(--font-poppins)] text-base">FishPrice.LK</div>
            <p className="mt-1 text-sm text-brand-neutral">
              Price predictions for Peliyagoda fish market.
            </p>
          </div>

          <div className="flex flex-wrap gap-4 text-sm">
            <Link className="text-slate-700 hover:text-brand-secondary" href="/#contact">
              Contact
            </Link>
            <Link className="text-slate-700 hover:text-brand-secondary" href="/#data-sources">
              Data Sources
            </Link>
            <Link className="text-slate-700 hover:text-brand-secondary" href="/#disclaimer">
              Disclaimer
            </Link>
          </div>
        </div>

        <div className="mt-6 text-xs text-brand-neutral">
          © {new Date().getFullYear()} FishPrice.LK. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
