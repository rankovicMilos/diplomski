import { ListItemType } from "../components/ExpandableList/ExpandableListItem";

// TODO: hardcoded for now, will be read from the database.
// Label convention: "<code> - <name>" (the code is the first token of the label).
const naceCategories: ListItemType[] = [
  {
      label: "A - Agriculture, forestry and fishing",
      items: [
        {
          label: "A1 - Crop and animal production, hunting and related service activities",
          items: [
            {
              label: "A1.1 - Growing of non-perennial crops",
              items: [
                {
                  label: "A1.11 Growing of cereals, other than rice, leguminous crops and oil seeds (en)",
                  items: []
                },
                {
                  label: "A1.12 Growing of rice",
                  items: []
                }
              ]
            },
          ]
        },
      ]
    },
  // TODO: temporarily hidden on FE, only A, D (Electricity) and K (Telecom) are shown for now
  // {
  //   label: "C - Manufacturing",
  //   items: [
  //     {
  //       label: "C17 - Manufacture of paper and paper products",
  //       items: [
  //         {
  //           label: "C17.2 - Manufacture of articles of paper and paperboard",
  //           items: [
  //             {
  //               label: "C17.21 Manufacture of corrugated paper and paperboard and of containers of paper and paperboard",
  //               items: []
  //             }
  //           ]
  //         }
  //       ]
  //     },
  //     {
  //       label: "C19 - Manufacture of coke and refined petroleum products",
  //       items: [
  //         {
  //           label: "C19.2 - Manufacture of refined petroleum products",
  //           items: [
  //             {
  //               label: "C19.20 Manufacture of refined petroleum products",
  //               items: []
  //             }
  //           ]
  //         }
  //       ]
  //     },
  //     {
  //       label: "C20 - Manufacture of chemicals and chemical products",
  //       items: [
  //         {
  //           label: "C20.1 - Manufacture of basic chemicals, fertilisers and nitrogen compounds, plastics and synthetic rubber in primary forms",
  //           items: [
  //             {
  //               label: "C20.15 Manufacture of fertilisers and nitrogen compounds",
  //               items: []
  //             }
  //           ]
  //         }
  //       ]
  //     },
  //     {
  //       label: "C21 - Manufacture of basic pharmaceutical products and pharmaceutical preparations",
  //       items: [
  //         {
  //           label: "C21.2 - Manufacture of pharmaceutical preparations",
  //           items: [
  //             {
  //               label: "C21.20 Manufacture of pharmaceutical preparations",
  //               items: []
  //             }
  //           ]
  //         }
  //       ]
  //     },
  //     {
  //       label: "C22 - Manufacture of rubber and plastic products",
  //       items: [
  //         {
  //           label: "C22.2 - Manufacture of plastic products",
  //           items: [
  //             {
  //               label: "C22.22 Manufacture of plastic packing goods",
  //               items: []
  //             }
  //           ]
  //         }
  //       ]
  //     },
  //     {
  //       label: "C24 - Manufacture of basic metals",
  //       items: [
  //         {
  //           label: "C24.1 - Manufacture of basic iron and steel and of ferro-alloys",
  //           items: [
  //             {
  //               label: "C24.10 Manufacture of basic iron and steel and of ferro-alloys",
  //               items: []
  //             }
  //           ]
  //         }
  //       ]
  //     },
  //   ]
  // },
  {
    label: "D - Electricity, gas, steam and air conditioning supply",
    items: [
      {
        label: "D35 - Electricity, gas, steam and air conditioning supply",
        items: [
          // Official Electricity codes (NACE Rev. 2.1), source: "Nace za industrije.xlsx"
          {
            label: "D35.10 - Production, transmission, and distribution of electricity",
            items: [
              {
                label: "D35.11 Production of electricity from non-renewable sources",
                items: []
              },
              {
                label: "D35.12 Production of electricity from renewable sources",
                items: []
              },
              {
                label: "D35.13 Transmission of electricity",
                items: []
              },
              {
                label: "D35.14 Distribution of electricity",
                items: []
              },
              {
                label: "D35.15 Trade of electricity",
                items: []
              },
              {
                label: "D35.16 Storage of electricity",
                items: []
              }
            ]
          },
          {
            label: "D35.40 Activities of brokers and agents for electric power and natural gas",
            items: []
          }
        ]
      }
    ]
  },
  // {
  //   label: "F - Construction",
  //   items: [
  //     {
  //       label: "F41 - Construction of buildings",
  //       items: [
  //         {
  //           label: "F41.2 - Construction of residential and non-residential buildings",
  //           items: [
  //             {
  //               label: "F41.20 Construction of residential and non-residential buildings",
  //               items: []
  //             }
  //           ]
  //         }
  //       ]
  //     }
  //   ]
  // },
  // {
  //   label: "G - Wholesale and retail trade; repair of motor vehicles and motorcycles",
  //   items: [
  //     {
  //       label: "G46 - Wholesale trade, except of motor vehicles and motorcycles",
  //       items: []
  //     },
  //     {
  //       label: "G47 - Retail trade, except of motor vehicles and motorcycles",
  //       items: []
  //     }
  //   ]
  // },
  // {
  //   label: "J - Information and communication",
  //   items: [
  //     {
  //       label: "J61 - Telecommunications",
  //       items: []
  //     },
  //     {
  //       label: "J62 - Computer programming, consultancy and related activities",
  //       items: []
  //     }
  //   ]
  // },
  // Telecom codes (NACE Rev. 2.1), source: "Nace za industrije.xlsx"
  // All grouped under K so the whole industry sits under one letter. Officially 26 and 27 belong to section C (Manufacturing).
  {
    label: "K - Telecommunication, computer programming, consulting, computing infrastructure and other information service activities",
    items: [
      {
        label: "K26 - Manufacture of computer, electronic and optical products",
        items: [
          {
            label: "K26.30 Manufacture of communication equipment",
            items: []
          }
        ]
      },
      {
        label: "K27 - Manufacture of electrical equipment",
        items: [
          {
            label: "K27.30 - Manufacture of optical and electrical cables, electrical conductors, and electrical installation equipment",
            items: [
              {
                label: "K27.31 Manufacture of fibre optic cables",
                items: []
              },
              {
                label: "K27.32 Manufacture of other electronic and electric wires and cables",
                items: []
              },
              {
                label: "K27.33 Manufacture of wiring devices",
                items: []
              }
            ]
          }
        ]
      },
      {
        label: "K61 - Telecommunication",
        items: [
          {
            label: "K61.00 - Telecommunications activities",
            items: [
              {
                label: "K61.10 Wired, wireless, and satellite telecommunication activities",
                items: []
              },
              {
                label: "K61.90 Other telecommunication activities",
                items: []
              }
            ]
          }
        ]
      }
    ]
  },
  // {
  //   label: "L - Real estate activities",
  //   items: [
  //     {
  //       label: "L68 - Real estate activities",
  //       items: []
  //     }
  //   ]
  // },
]

export const getNaceCode = (label: string) => label.split(' ')[0];

// Labels from the root down to the item with the given code, e.g. ["D - ...", "D35 - ...", "D35.10 - ...", "D35.12 ..."].
// Walks the tree instead of comparing codes, because D35.11 sits under D35.10 without being its string prefix.
export const findNacePath = (code: string, list: ListItemType[] = naceCategories): string[] => {
  for (const item of list) {
    if (getNaceCode(item.label) === code) return [item.label];
    const childPath = findNacePath(code, item.items);
    if (childPath.length) return [item.label, ...childPath];
  }
  return [];
}

export const findNaceLabel = (code: string, list: ListItemType[] = naceCategories): string | undefined =>
  findNacePath(code, list).at(-1);

// Keeps items whose label matches the query (code or name), plus their ancestors.
// An item that matches keeps all its children, so the whole branch stays browsable.
export const filterNaceTree = (query: string, list: ListItemType[] = naceCategories): ListItemType[] => {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) return list;

  return list.flatMap(item => {
    if (item.label.toLowerCase().includes(normalizedQuery)) return [item];
    const items = filterNaceTree(normalizedQuery, item.items);
    return items.length ? [{ ...item, items }] : [];
  });
}

export default naceCategories;
