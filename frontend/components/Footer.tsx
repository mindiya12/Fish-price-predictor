import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-black/5 bg-white">
      <div className="mx-auto w-full max-w-6xl px-4 py-12">
        <div className="flex flex-col gap-8 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="font-semibold text-brand-primary">FishPrice.LK</div>
            <p className="mt-2 text-sm text-brand-neutral">
              AI-powered price predictions for Peliyagoda fish market.
            </p>
          </div>

          <div className="flex flex-wrap gap-6 text-sm">
            <Link className="text-brand-neutral hover:text-brand-primary transition" href="/#contact">
              Contact
            </Link>
            <Link className="text-brand-neutral hover:text-brand-primary transition" href="/#data-sources">
              Data Sources
            </Link>
            <Link className="text-brand-neutral hover:text-brand-primary transition" href="/#disclaimer">
              Disclaimer
            </Link>
          </div>
        </div>

        <div className="mt-8 border-t border-black/5 pt-6 text-xs text-brand-neutral">
          © {new Date().getFullYear()} FishPrice.LK. All rights reserved. Made for Sri Lankan fish markets.
        </div>
      </div>
    </footer>
  );
}
