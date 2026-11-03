// TODO: hardcoded for now, will be read from the database.
// Industry ids mirror `industry:` in backend/scraper-lambda/src/config/sources/*.yaml

import { findNacePath } from "./naceCategories";

export type IndustrySection = {
  id: string,
  title: string,
  subsections: string[]
}

export type Industry = {
  id: string,
  name: string,
  naceCodes: string[],
  // Category the backend already has a generated market analysis for.
  // The industry id reads the report from industry_analysis/<id>/, anything else the crop market analysis.
  analysisCategory?: string,
  sections: IndustrySection[]
}

const industries: Industry[] = [
  {
    id: "cereals",
    name: "Žitarice",
    naceCodes: ["A1.11"],
    analysisCategory: "A1.11 Growing of cereals, other than rice, leguminous crops and oil seeds (en)",
    sections: []
  },
  {
    id: "paper_packaging",
    name: "Papirna ambalaža",
    naceCodes: ["C17.21"],
    sections: []
  },
  {
    id: "fuel",
    name: "Gorivo",
    naceCodes: ["C19.20"],
    sections: []
  },
  {
    id: "fertilizers",
    name: "Đubriva",
    naceCodes: ["C20.15"],
    sections: []
  },
  {
    id: "pharmaceuticals",
    name: "Farmaceutika",
    naceCodes: ["C21.20"],
    sections: []
  },
  {
    id: "plastic_packaging",
    name: "Plastična ambalaža",
    naceCodes: ["C22.22"],
    sections: []
  },
  {
    id: "steel",
    name: "Čelik",
    naceCodes: ["C24.10"],
    sections: []
  },
  {
    id: "electricity",
    name: "Električna energija",
    naceCodes: ["D35.10", "D35.11", "D35.12", "D35.13", "D35.14", "D35.15", "D35.16", "D35.40"],
    analysisCategory: "electricity",
    sections: [
      {
        id: "market_analysis",
        title: "Analiza tržišta",
        subsections: [
          "Uvodni pasus",
          "Grafik proizvodnje 2010–2024",
          "Fossil fuel production",
          "New coal still on the cards despite climate vulnerability",
          "Hydropower hassle",
          "Renewable energy and energy efficiency",
        ]
      },
      {
        id: "price_analysis",
        title: "Analiza cena",
        subsections: [
          "Electricity price statistics",
        ]
      },
    ]
  },
  {
    id: "construction",
    name: "Građevinarstvo",
    naceCodes: ["F41"],
    sections: []
  },
  {
    id: "retail_wholesale",
    name: "Trgovina na malo i veliko",
    naceCodes: ["G46", "G47"],
    sections: []
  },
  {
    id: "telecom",
    name: "Telekomunikacije",
    naceCodes: ["K26.30", "K27.30", "K27.31", "K27.32", "K27.33", "K61.00", "K61.10", "K61.90"],
    sections: []
  },
  {
    id: "it",
    name: "IT",
    naceCodes: ["J62"],
    sections: []
  },
  {
    id: "real_estate",
    name: "Nekretnine",
    naceCodes: ["L68"],
    sections: []
  },
]

export const getIndustryById = (id: string) => industries.find(industry => industry.id === id);

// A NACE code is linked to an industry when one is an ancestor of (or equal to) the other,
// e.g. "D", "D35" and "D35.11" all resolve to electricity.
// Codes hidden from the NACE tree are skipped, so "C" does not resolve to industries that are not shown yet.
export const getIndustriesForNaceCode = (code: string) => {
  if (!code) return [];
  return industries.filter(industry =>
    industry.naceCodes.some(naceCode =>
      (naceCode.startsWith(code) || code.startsWith(naceCode)) && findNacePath(naceCode).length > 0
    )
  );
}

export default industries;
