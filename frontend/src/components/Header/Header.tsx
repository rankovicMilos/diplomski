import logo from "@/public/logo.svg"
import Image from "next/image";
import Link from "next/link";

const Header = () => {
  return (
    <header className="bg-white-100 h-20 w-100 flex items-center justify-between px-16 border-b-2 border-charcoal-25 gap-6 sticky top-0 z-50">
      <Link href="/">
        <Image
          src={logo}
          alt="Analiza sektorskog rizika"
          height={40}
          priority
        />
      </Link>
    </header>
  )

}

export default Header;