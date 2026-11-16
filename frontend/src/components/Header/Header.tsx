import logo from "@/public/ftn_logo_white.svg";
import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";
import Navigation from "../Navigation/Navigation";

const Header = () => {
	return (
		<header className="w-100 sticky top-0 z-50 flex h-16 items-center justify-center bg-charcoal-100 px-4 shadow-medium md:px-8">
			<div className="flex w-full max-w-[1200px] items-center justify-between gap-4">
				<Link
					href="/"
					className="flex items-center gap-3 rounded-xs text-white-100 hover:text-white-100 hover:no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white-100"
				>
					<Image
						src={logo}
						alt="FTN"
						height={44}
						priority
					/>
					<span className="hidden text-md font-semibold tracking-tight sm:block">Analiza sektorskog rizika</span>
				</Link>
				<Suspense>
					<Navigation />
				</Suspense>
			</div>
		</header>
	);
};

export default Header;
