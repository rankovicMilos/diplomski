import type { Config } from "tailwindcss";
import containerConfig from "@tailwindcss/container-queries"
import scrollbar from "tailwind-scrollbar";

const config: Config = {
	plugins: [containerConfig, scrollbar({nocompatible: true})],
	content: [
		"./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/components/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/app/**/*.{js,ts,jsx,tsx,mdx}"
	],
	theme: {
		borderRadius: {
			"none": "0",
			"2xs": ".25rem",
			"xs": ".5rem",
			"sm": "1rem",
			"md": "1.5rem",
			"lg": "2rem",
			"xl": "3rem",
			"full": "9999px"
		},
		
		boxShadow: {
			"low": "2px 2px 4px 0px rgba(0, 0, 0, 0.2)",
			"medium": "0px 4px 10px 0px rgba(0, 0, 0, 0.24)",
			"high": "0px 4px 30px 0px rgba(0, 0, 0, 0.15)",
			"high-lighter": "0px 4px 48px 0px rgba(0, 0, 0, 0.07)",
			"light": "0px 2px 6px 0px rgba(0, 0, 0, 0.08)",
			"none": "none"
		},
		colors: {
			yellow: {
				100: "#FFDC00",
				90: "#FFDF1A",
				80: "#FFE333",
				75: "#FFE540",
				70: "#FFE74D",
				60: "#FFEA66",
				50: "#FFED7F",
				40: "#FFF199",
				30: "#FFF5B3",
				25: "#FFF6BF",
				20: "#FFF8CC",
				10: "#FFFDF2"
			},
			charcoal: {
				100: "#2F2F2F",
				90: "#444444",
				80: "#585858",
				75: "#666666",
				70: "#6D6D6D",
				60: "#828282",
				50: "#989898",
				40: "#ACACAC",
				30: "#C1C1C1",
				25: "#CBCBCB",
				20: "#D5D5D5",
				10: "#EAEAEA"
			},
			white: {
				100: "#FFFFFF",
				"80T": "#ffffffcc"
			},
			teal: {
				100: "#62BAB7",
				90: "#72C1BE",
				80: "#81C8C5",
				75: "#89CBC9",
				70: "#91CFCD",
				60: "#A1D6D4",
				50: "#B0DCDB",
				40: "#C0E3E2",
				30: "#D0EAE9",
				25: "#D7EEED",
				20: "#E0F1F1",
				10: "#EFF8F8"
			},
			steel: {
				100: "#CFD1D4",
				90: "#D4D6D8",
				80: "#D8DADD",
				75: "#DBDDDF",
				70: "#DDDFE1",
				60: "#E2E3E5",
				50: "#E7E8EA",
				40: "#ECEDEE",
				30: "#F1F1F2",
				25: "#F3F4F4",
				20: "#F5F6F6",
				10: "#FAFAFB"
			},
			orange: {
				100: "#F7A71B",
				75: "#F8BD54",
				50: "#FAD38C",
				25: "#FDE9C5"
			},
			purple: {
				100: "#B58BBA",
				75: "#C7A8CB",
				50: "#DAC5DC",
				25: "#ECE2EE",
				10: "#ECE2EE50"
			},
			red: {
				100: "#CE492C",
				75: "#DA7761",
				50: "#E7A495",
				25: "#F3D2CA"
			},
			green: {
				100: "#3C7D1A",
				75: "#429715",
				20: "#CAE5BC",
				10: "#CAE5BC20",
			},
			warning: {
				100: "#C51315",
				20: "#F4D0D0"
			},
			success: {
				100: "#5ABC27",
				20: "#DEF1D4"
			},
			black: {
				100: "#000000"
			},
			transparent: "transparent",
			current: "currentColor"
		},
		fontFamily: {
			"lato": ["var(--font-lato)"],
			"open-sans": ["var(--font-open-sans)"]
		},
		fontSize: {
			"2xs": ["0.75rem", { lineHeight: "1.125rem" }],
			"xs": ["0.875rem", { lineHeight: "1.313rem" }],
			"sm": ["1rem", { lineHeight: "1.5rem" }],
			"base": ["1rem", { lineHeight: "1.5rem" }],
			"md": ["1.125rem", { lineHeight: "1.688rem" }],
			"lg": ["1.25rem", { lineHeight: "1.875rem" }],
			"xl": ["1.625rem", { lineHeight: "2.438rem" }],
			"2xl": ["1.875rem", { lineHeight: "2.813rem" }],
			"3xl": ["2rem", { lineHeight: "3rem" }],
			"4xl": ["2.25rem", { lineHeight: "3.375rem" }],
			"5xl": ["2.375rem", { lineHeight: "3.563rem" }],
			"6xl": ["3rem", { lineHeight: "4.5rem" }],
			"7xl": ["3.875rem", { lineHeight: "5.8125rem" }],
			"8xl": ["7.5rem", { lineHeight: "11.25rem" }]
		},
		screens: {
			"2xs": "375px",
			"xs": "425px",
			"sm": "640px",
			"md": "834px",
			"lg": "1024px",
			"xl": "1440px",
			"2xl": "2000px"
		},
		containers: {
			"2xs": "375px",
			"xs": "425px",
			"sm": "640px",
			"md": "834px",
			"lg": "1024px",
			"xl": "1440px",
			"2xl": "2000px"
		},
		extend: {
			
			transitionProperty: {
				"height": "height",
				"max-h": "max-h"
			},
			borderWidth: {
				"1": "1px",
				"3": "3px"
			},
			maxWidth: {
				"8xl": "90rem"
			},
			padding: {
				"30": "7.5rem"
			},
			margin: {
				"30": "7.5rem",
				"1/2": "50%"
			},
			lineHeight: {
				"150": "1.5",
				"130": "1.3",
				"120": "1.2"
			}
		}
	},
	future: {
		hoverOnlyWhenSupported: true
	}
};
export default config;
