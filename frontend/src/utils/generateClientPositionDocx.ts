import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  HeadingLevel,
  WidthType,
  AlignmentType,
  BorderStyle,
  ShadingType,
  TableLayoutType,
} from 'docx';
import { saveAs } from 'file-saver';
import { IMarketPositionReport, IPeerAnalysis, IMarketAnalysis } from '@/src/lib/api';
import capitalizeWords from './helpers/capitalizeWords';
import { groupBy } from './helpers/groupBy';

interface ClientPositionReport {
  market_position?: IMarketPositionReport;
  peer_analysis?: IPeerAnalysis | null;
  market_analysis?: IMarketAnalysis | null;
}

type MetricData = {
  metric_name_sr: string;
  metric_name_en: string;
  aop_code: string;
  companies: {
    name: string;
    value: number;
    market_share_pct: number;
    rank: number;
  }[];
  industry_total: number;
};

const TEAL_COLOR = '0D9488';
const CHART_HEADER_COLOR = '0EA5E9';
const DEFAULT_FONT = 'Calibri';
// Full page width in twips (1 inch = 1440 twips, standard page is 8.5" with 1" margins = 6.5" = 9360 twips)
const FULL_PAGE_WIDTH_TWIPS = 9360;

type CommodityAnalyzed = IMarketPositionReport['commodities_analyzed'][number];

type TableData = {
  id: string;
  title: string;
  columns: {
    id: string;
    name: string;
    type: string;
  }[];
  rows: (string | number | null)[][];
};

type ChartData = {
  id: string;
  title: string;
  type: string;
  data: {
    label: string;
    value: number;
  }[];
};

const createHeading = (text: string, level: (typeof HeadingLevel)[keyof typeof HeadingLevel]) => {
  return new Paragraph({
    children: [
      new TextRun({
        text,
        font: DEFAULT_FONT,
      }),
    ],
    heading: level,
    spacing: { before: 200, after: 100 },
  });
};

const createLabelValue = (label: string, value: string) => {
  return new Paragraph({
    children: [
      new TextRun({ text: `${label}: `, bold: true, font: DEFAULT_FONT }),
      new TextRun({ text: value, font: DEFAULT_FONT }),
    ],
    spacing: { after: 100 },
  });
};

const createBulletPoint = (text: string) => {
  return new Paragraph({
    children: [
      new TextRun({ text, font: DEFAULT_FONT }),
    ],
    bullet: { level: 0 },
    spacing: { after: 50 },
  });
};

const createNumberedItem = (text: string, index: number) => {
  return new Paragraph({
    children: [
      new TextRun({ text: `${index + 1}. ${text}`, font: DEFAULT_FONT }),
    ],
    spacing: { after: 50 },
  });
};

const createTableCell = (text: string | undefined, isHeader = false, widthTwips?: number) => {
  return new TableCell({
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text: text ?? '',
            bold: isHeader,
            size: isHeader ? 22 : 20,
            font: DEFAULT_FONT,
          }),
        ],
        alignment: AlignmentType.CENTER,
      }),
    ],
    shading: isHeader
      ? { fill: TEAL_COLOR, type: ShadingType.CLEAR, color: 'auto' }
      : undefined,
    width: widthTwips ? { size: widthTwips, type: WidthType.DXA } : undefined,
  });
};

const createDivider = () => {
  return new Paragraph({
    children: [],
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 6, color: 'CCCCCC' },
    },
    spacing: { before: 200, after: 200 },
  });
};

const isYear = (num: number) => {
  return num >= 2000 && num <= 2100 && Number.isInteger(num);
};

const formatNumber = (num: number) => {
  if (isYear(num)) {
    return num.toString();
  }
  return new Intl.NumberFormat('en-US').format(num);
};

const formatValue = (value: string | number | null): string => {
  if (value === null) return '-';
  if (typeof value === 'number') {
    return formatNumber(value);
  }
  // Check if string is a year-like number
  const numValue = Number(value);
  if (!isNaN(numValue) && isYear(numValue)) {
    return value.toString();
  }
  return value.toString();
};

const formatCurrency = (num: number) => {
  if (num >= 1e9) {
    return (num / 1e9).toFixed(1) + 'B';
  }
  if (num >= 1e6) {
    return (num / 1e6).toFixed(1) + 'M';
  }
  return formatNumber(num);
};

const generateDataTable = (table: TableData): (Paragraph | Table)[] => {
  const elements: (Paragraph | Table)[] = [];

  // Table title - keepNext keeps it with the table
  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: table.title,
          bold: true,
          size: 22,
          color: TEAL_COLOR,
          font: DEFAULT_FONT,
        }),
      ],
      spacing: { before: 150, after: 100 },
      keepNext: true,
    })
  );

  // Create table
  const columnCount = table.columns.length;
  const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / columnCount);

  const years = [...new Set(table.rows.map(row => row[1]))].map(year => `${year}`)
  let cols = table.columns.map(col => col.name);
  if (table.id === "production_stats") cols = ["Crop", ...years, ...table.columns.filter(col => col.id !== 'crop' && col.id !== "year").map(col => col.name)]

  const headerRow = new TableRow({
    children: cols.map((col) => createTableCell(col, true, cellWidth)),
    cantSplit: true,
  });

  const groupedCrops = groupBy(table.rows, (row) => row[0] || "")
  let rows = table.rows
  if (table.id === "production_stats") rows = Object.entries(groupedCrops).map(([key, crops]) => [key, ...crops.map(crop => crop.slice(2)).flat()])

  const dataRows = rows.map(
    (row) =>
      new TableRow({
        children: row.map((cell) =>
          createTableCell(formatValue(cell), false, cellWidth)
        ),
        cantSplit: true,
      })
  );

  elements.push(
    new Table({
      width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
      layout: TableLayoutType.FIXED,
      rows: [headerRow, ...dataRows],
    })
  );

  return elements;
};

const generateChartAsTable = (chart: ChartData): (Paragraph | Table)[] => {
  const elements: (Paragraph | Table)[] = [];

  // Chart title with type indicator - keepNext keeps it with the table
  const chartTypeLabel = chart.type === 'pie' ? '(Pie Chart)' : chart.type === 'line' ? '(Line Chart)' : chart.type === 'bar' ? '(Bar Chart)' : '';
  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: `${chart.title} ${chartTypeLabel}`,
          bold: true,
          size: 22,
          color: CHART_HEADER_COLOR,
          font: DEFAULT_FONT,
        }),
      ],
      spacing: { before: 150, after: 100 },
      keepNext: true,
    })
  );

  // For pie/bar charts, display as simple label-value table
  if (chart.type === 'pie' || chart.type === 'bar') {
    const colCount = 3;
    const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

    const headerRow = new TableRow({
      children: [
        createTableCell('Label', true, cellWidth),
        createTableCell('Value', true, cellWidth),
        createTableCell('Percentage', true, cellWidth),
      ],
      cantSplit: true,
    });

    const total = chart.data.reduce((sum, item) => sum + item.value, 0);
    const dataRows = chart.data.map(
      (item) =>
        new TableRow({
          children: [
            createTableCell(item.label, false, cellWidth),
            createTableCell(formatNumber(item.value), false, cellWidth),
            createTableCell(total > 0 ? `${((item.value / total) * 100).toFixed(1)}%` : '0%', false, cellWidth),
          ],
          cantSplit: true,
        })
    );

    elements.push(
      new Table({
        width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
        layout: TableLayoutType.FIXED,
        rows: [headerRow, ...dataRows],
      })
    );
  }

  // For line charts, group by category and show trends
  if (chart.type === 'line') {
    // Data label format: 'crop year' - group by crop
    const grouped: Record<string, { year: string; value: number }[]> = {};
    chart.data.forEach((item) => {
      const parts = item.label.split(' ');
      const crop = parts[0];
      const year = parts[1] || '';
      if (!grouped[crop]) {
        grouped[crop] = [];
      }
      grouped[crop].push({ year, value: item.value });
    });

    const years = [...new Set(chart.data.map((item) => item.label.split(' ')[1]))].filter(Boolean);

    if (years.length > 0) {
      const colCount = years.length + 1; // Category + years
      const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

      const headerRow = new TableRow({
        children: [
          createTableCell('Category', true, cellWidth),
          ...years.map((year) => createTableCell(year, true, cellWidth)),
        ],
        cantSplit: true,
      });

      const dataRows = Object.entries(grouped).map(
        ([category, values]) =>
          new TableRow({
            children: [
              createTableCell(category, false, cellWidth),
              ...years.map((year) => {
                const match = values.find((v) => v.year === year);
                return createTableCell(match ? formatNumber(match.value) : '-', false, cellWidth);
              }),
            ],
            cantSplit: true,
          })
      );

      elements.push(
        new Table({
          width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
          layout: TableLayoutType.FIXED,
          rows: [headerRow, ...dataRows],
        })
      );
    } else {
      // Simple list if no year grouping
      const colCount = 2;
      const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

      const headerRow = new TableRow({
        children: [
          createTableCell('Label', true, cellWidth),
          createTableCell('Value', true, cellWidth),
        ],
        cantSplit: true,
      });

      const dataRows = chart.data.map(
        (item) =>
          new TableRow({
            children: [
              createTableCell(item.label, false, cellWidth),
              createTableCell(formatNumber(item.value), false, cellWidth),
            ],
            cantSplit: true,
          })
      );

      elements.push(
        new Table({
          width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
          layout: TableLayoutType.FIXED,
          rows: [headerRow, ...dataRows],
        })
      );
    }
  }

  return elements;
};

const generateCommodityEstimateTable = (commodity: CommodityAnalyzed): Table => {
  const colCount = 3;
  const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

  return new Table({
    width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    rows: [
      new TableRow({
        children: [
          createTableCell('Scenario', true, cellWidth),
          createTableCell('Estimated Volume', true, cellWidth),
          createTableCell('Market Share', true, cellWidth),
        ],
        cantSplit: true,
      }),
      new TableRow({
        children: [
          createTableCell('Low Estimate', false, cellWidth),
          createTableCell(formatNumber(commodity.estimated_volume.low_estimate_tonnes), false, cellWidth),
          createTableCell(`${commodity.market_share.low_estimate_pct}%`, false, cellWidth),
        ],
        cantSplit: true,
      }),
      new TableRow({
        children: [
          createTableCell('Mid Estimate', false, cellWidth),
          createTableCell(formatNumber(commodity.estimated_volume.mid_estimate_tonnes), false, cellWidth),
          createTableCell(`${commodity.market_share.mid_estimate_pct}%`, false, cellWidth),
        ],
        cantSplit: true,
      }),
      new TableRow({
        children: [
          createTableCell('High Estimate', false, cellWidth),
          createTableCell(formatNumber(commodity.estimated_volume.high_estimate_tonnes), false, cellWidth),
          createTableCell(`${commodity.market_share.high_estimate_pct}%`, false, cellWidth),
        ],
        cantSplit: true,
      }),
    ],
  });
};


const generateMarketAnalysisSection = (analysis: IMarketAnalysis): (Paragraph | Table)[] => {
  const elements: (Paragraph | Table)[] = [];

  // Main Title
  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: 'Sector Analysis Report',
          bold: true,
          size: 36,
          color: TEAL_COLOR,
          font: DEFAULT_FONT,
        }),
      ],
      spacing: { after: 100 },
    })
  );

  // Analysis period and currency
  elements.push(createLabelValue('Analysis period', analysis.meta.period));
  elements.push(createDivider());

  // Sector Title
  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: capitalizeWords(analysis.meta.sector),
          bold: true,
          size: 28,
          color: TEAL_COLOR,
          font: DEFAULT_FONT,
        }),
      ],
      spacing: { after: 100 },
    })
  );

  // Meta information
  elements.push(
    createLabelValue('Date generated', new Date(analysis.generated_at).toLocaleDateString())
  );
  elements.push(createLabelValue('Period', analysis.meta.period));
  elements.push(createLabelValue('Country', analysis.meta.country));
  elements.push(createLabelValue('Sector', analysis.meta.sector));
  elements.push(createDivider());

  // Sections
  analysis.sections.forEach((section, index) => {
    elements.push(createHeading(section.title, HeadingLevel.HEADING_2));

    // Process content line by line
    const contentLines = section.content_md
      .replace(/#{1,6}\s/g, '')
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .split('\n');

    contentLines.forEach((line) => {
      const trimmedLine = line.trim();
      if (!trimmedLine) return;

      // Check for table placeholder
      const lineTableMatch = trimmedLine.match(/\{\{table:(\w+)\}\}/);
      if (lineTableMatch) {
        const lineTableId = lineTableMatch[1];
        const table = analysis.tables?.find((t) => t.id === lineTableId);
        if (table) {
          elements.push(...generateDataTable(table));
        }
        return;
      }

      // Regular text line
      elements.push(
        new Paragraph({
          children: [
            new TextRun({ text: trimmedLine, font: DEFAULT_FONT }),
          ],
          spacing: { after: 100 },
        })
      );
    });

    if (index !== analysis.sections.length - 1) {
      elements.push(createDivider());
    }
  });

  elements.push(createDivider());

  // Charts as tables
  analysis.charts.forEach((chart) => {
    elements.push(...generateChartAsTable(chart));
  });

  elements.push(createDivider());

  // Sources
  elements.push(createHeading('Sources', HeadingLevel.HEADING_2));
  analysis.sources.forEach((source) => {
    elements.push(createBulletPoint(`${source.name} ${source.date}`));
  });

  // Page break after market analysis
  elements.push(
    new Paragraph({
      children: [],
      pageBreakBefore: true,
    })
  );

  return elements;
};

const generateMarketPositionSection = (marketPosition: IMarketPositionReport): (Paragraph | Table)[] => {
  const elements: (Paragraph | Table)[] = [];

  // Title
  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: 'Market Position Analysis',
          bold: true,
          size: 36,
          color: TEAL_COLOR,
          font: DEFAULT_FONT,
        }),
      ],
      spacing: { after: 200 },
    })
  );

  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: marketPosition.client_name,
          bold: true,
          size: 32,
          color: TEAL_COLOR,
          font: DEFAULT_FONT,
        }),
      ],
      spacing: { after: 100 },
    })
  );

  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: 'Market and Price Analysis Report',
          font: DEFAULT_FONT,
        }),
      ],
      heading: HeadingLevel.HEADING_3,
      spacing: { after: 200 },
    })
  );

  // Basic info
  elements.push(createLabelValue('Client name', marketPosition.client_name));
  elements.push(createLabelValue('Analysis period', marketPosition.analysis_period));
  elements.push(createLabelValue('Currency', marketPosition.currency));
  elements.push(createDivider());

  // Analysis narrative (convert markdown to plain text and include tables/charts)
  if (marketPosition.analysis_narrative_md) {
    elements.push(createHeading('Analysis Narrative', HeadingLevel.HEADING_2));

    const narrativeLines = marketPosition.analysis_narrative_md
      .replace(/#{1,6}\s/g, '')
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .split('\n');

    narrativeLines.forEach((line) => {
      const trimmedLine = line.trim();
      if (!trimmedLine) return;

      // Check for table placeholder
      const tableMatch = trimmedLine.match(/\{\{table:(\w+)\}\}/);
      if (tableMatch) {
        const tableId = tableMatch[1];
        const table = marketPosition.tables?.find((t) => t.id === tableId);
        if (table) {
          elements.push(...generateDataTable(table));
        }
        return;
      }

      // Check for chart placeholder
      const chartMatch = trimmedLine.match(/\{\{chart:(\w+)\}\}/);
      if (chartMatch) {
        const chartId = chartMatch[1];
        const chart = marketPosition.charts?.find((c) => c.id === chartId);
        if (chart) {
          elements.push(...generateChartAsTable(chart));
        }
        return;
      }

      // Regular text line
      elements.push(
        new Paragraph({
          children: [
            new TextRun({ text: trimmedLine, font: DEFAULT_FONT }),
          ],
          spacing: { after: 100 },
        })
      );
    });
    elements.push(createDivider());
  }

  // Commodities Analyzed
  const commodities = marketPosition.commodities_analyzed;
  if (commodities && commodities.length > 0) {
    elements.push(createHeading('Commodities Analyzed', HeadingLevel.HEADING_2));

    commodities.forEach((commodity) => {
      // Commodity header
      elements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: capitalizeWords(commodity.commodity),
              bold: true,
              size: 26,
              color: TEAL_COLOR,
              font: DEFAULT_FONT,
            }),
          ],
          spacing: { before: 150, after: 100 },
        })
      );

      elements.push(createLabelValue('Revenue share percentage', `${commodity.revenue_share_pct}%`));
      elements.push(
        createLabelValue(
          'Estimated revenue',
          `${formatNumber(commodity.estimated_revenue.value)} ${commodity.estimated_revenue.unit}`
        )
      );

      // Volume & Market Share table
      elements.push(
        new Paragraph({
          children: [
            new TextRun({ text: 'Volume & Market Share Estimation', font: DEFAULT_FONT }),
          ],
          heading: HeadingLevel.HEADING_4,
          spacing: { before: 100, after: 50 },
        })
      );
      elements.push(generateCommodityEstimateTable(commodity));

      // Market Data
      const marketData = commodity.market_data;
      elements.push(
        new Paragraph({
          children: [
            new TextRun({ text: 'Market Overview', font: DEFAULT_FONT }),
          ],
          heading: HeadingLevel.HEADING_4,
          spacing: { before: 150, after: 50 },
        })
      );
      elements.push(createLabelValue('Total production', `${formatNumber(marketData.total_production_tonnes)} tonnes`));
      elements.push(createLabelValue('Harvested area', `${formatNumber(marketData.harvested_area_ha)} hectares`));
      elements.push(createLabelValue('Yield per hectare', `${formatNumber(marketData.yield_per_ha)} tonnes/ha`));
      elements.push(
        createLabelValue(
          'Total market value',
          `${formatCurrency(marketData.total_market_value.value)} ${marketData.total_market_value.unit}`
        )
      );

      // Price data
      elements.push(
        new Paragraph({
          children: [
            new TextRun({ text: 'Price Analysis', font: DEFAULT_FONT }),
          ],
          heading: HeadingLevel.HEADING_4,
          spacing: { before: 100, after: 50 },
        })
      );
      elements.push(createLabelValue('Average price', `${formatNumber(marketData.price_data.average_price)} ${marketData.price_data.price_unit}`));
      elements.push(
        createLabelValue(
          'Price range',
          `${formatNumber(marketData.price_data.price_range_low)} - ${formatNumber(marketData.price_data.price_range_high)} ${marketData.price_data.price_unit}`
        )
      );

      elements.push(createDivider());
    });
  }

  // Weighted Market Position
  const weightedPosition = marketPosition.weighted_market_position;
  if (weightedPosition) {
    elements.push(createHeading('Weighted Market Position', HeadingLevel.HEADING_2));
    elements.push(
      new Paragraph({
        children: [
          new TextRun({ text: weightedPosition.methodology, font: DEFAULT_FONT }),
        ],
        spacing: { after: 100 },
      })
    );

    const colCount = 3;
    const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

    elements.push(
      new Table({
        width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
        layout: TableLayoutType.FIXED,
        rows: [
          new TableRow({
            children: [
              createTableCell('Low Estimate', true, cellWidth),
              createTableCell('Mid Estimate', true, cellWidth),
              createTableCell('High Estimate', true, cellWidth),
            ],
            cantSplit: true,
          }),
          new TableRow({
            children: [
              createTableCell(`${weightedPosition.weighted_market_share.low_estimate_pct}%`, false, cellWidth),
              createTableCell(`${weightedPosition.weighted_market_share.mid_estimate_pct}%`, false, cellWidth),
              createTableCell(`${weightedPosition.weighted_market_share.high_estimate_pct}%`, false, cellWidth),
            ],
            cantSplit: true,
          }),
        ],
      })
    );

    elements.push(
      createLabelValue('Calculation basis', weightedPosition.calculation_basis.replaceAll('_share', ''))
    );
    elements.push(createDivider());
  }

  // Market Position Analysis
  const analysis = marketPosition.market_position_analysis;
  if (analysis) {
    elements.push(createHeading('Market Position Analysis', HeadingLevel.HEADING_2));
    elements.push(
      new Paragraph({
        children: [
          new TextRun({ text: analysis.methodology, font: DEFAULT_FONT }),
        ],
        spacing: { after: 100 },
      })
    );

    elements.push(createHeading('Assumptions', HeadingLevel.HEADING_3));
    analysis.assumptions.forEach((assumption) => {
      elements.push(createBulletPoint(assumption));
    });
    elements.push(createDivider());
  }

  // Client Financials Summary
  const financials = marketPosition.client_financials_summary;
  elements.push(createHeading('Client Financials Summary', HeadingLevel.HEADING_2));
  elements.push(
    createLabelValue(
      `Total revenue for year ${financials.total_revenue.year}`,
      `${formatNumber(financials.total_revenue.value)} ${financials.total_revenue.unit}`
    )
  );
  elements.push(
    new Paragraph({
      children: [
        new TextRun({ text: financials.revenue_trend, font: DEFAULT_FONT }),
      ],
      spacing: { after: 100 },
    })
  );
  elements.push(createDivider());

  // Limitations and Caveats
  elements.push(createHeading('Limitations and Caveats', HeadingLevel.HEADING_2));
  marketPosition.limitations_and_caveats.forEach((limitation) => {
    elements.push(createBulletPoint(limitation));
  });
  elements.push(createDivider());

  // Sources
  elements.push(createHeading('Sources', HeadingLevel.HEADING_2));
  marketPosition.sources.forEach((source) => {
    elements.push(
      createBulletPoint(`${source.name} (${source.type.replaceAll('_', ' ')})`)
    );
  });

  return elements;
};

const generateKeyMetricsTable = (
  companies: { name: string; value: number; market_share_pct: number; rank: number }[]
): Table => {
  const colCount = 4;
  const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

  return new Table({
    width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    rows: [
      new TableRow({
        children: [
          createTableCell('Company', true, cellWidth),
          createTableCell('Value (RSD)', true, cellWidth),
          createTableCell('Market Share', true, cellWidth),
          createTableCell('Rank', true, cellWidth),
        ],
        cantSplit: true,
      }),
      ...companies.map(
        (company) =>
          new TableRow({
            children: [
              createTableCell(capitalizeWords(company.name), false, cellWidth),
              createTableCell(formatNumber(company.value), false, cellWidth),
              createTableCell(`${company.market_share_pct}%`, false, cellWidth),
              createTableCell(company.rank?.toString(), false, cellWidth),
            ],
            cantSplit: true,
          })
      ),
    ],
  });
};

const generateCompanyProfilesTable = (
  companies: IPeerAnalysis['company_profiles']
): Table => {
  const mapToMillions = (val: number) => `${(val / 1000000).toFixed(2)}M`;
  const colCount = 6;
  const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

  return new Table({
    width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    rows: [
      new TableRow({
        children: [
          createTableCell('Company', true, cellWidth),
          createTableCell('Total Assets', true, cellWidth),
          createTableCell('Total Revenue', true, cellWidth),
          createTableCell('Op. Margin', true, cellWidth),
          createTableCell('Asset Turn.', true, cellWidth),
          createTableCell('Goods %', true, cellWidth),
        ],
        cantSplit: true,
      }),
      ...companies.map(
        (company) =>
          new TableRow({
            children: [
              createTableCell(capitalizeWords(company.name), false, cellWidth),
              createTableCell(mapToMillions(company.total_assets), false, cellWidth),
              createTableCell(mapToMillions(company.total_revenue), false, cellWidth),
              createTableCell(`${company.operating_margin_pct}%`, false, cellWidth),
              createTableCell(`${company.asset_turnover}x`, false, cellWidth),
              createTableCell(`${company.revenue_mix.goods_pct}%`, false, cellWidth),
            ],
            cantSplit: true,
          })
      ),
    ],
  });
};

const generateMarketStructureTable = (
  metrics: IPeerAnalysis['key_metrics_comparison']
): Table => {
  const mappedMetrics = (Object.values(metrics) as MetricData[]).map((value) => ({
    key: value.metric_name_en,
    value: value.industry_total,
  }));

  const colCount = 2;
  const cellWidth = Math.floor(FULL_PAGE_WIDTH_TWIPS / colCount);

  return new Table({
    width: { size: FULL_PAGE_WIDTH_TWIPS, type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    rows: [
      new TableRow({
        children: [
          createTableCell('Metric', true, cellWidth),
          createTableCell('Industry Total', true, cellWidth),
        ],
        cantSplit: true,
      }),
      ...mappedMetrics.map(
        (m) =>
          new TableRow({
            children: [
              createTableCell(m.key, false, cellWidth),
              createTableCell(formatNumber(m.value), false, cellWidth),
            ],
            cantSplit: true,
          })
      ),
    ],
  });
};

const generatePeerAnalysisSection = (
  peerAnalysis: IPeerAnalysis
): (Paragraph | Table)[] => {
  const elements: (Paragraph | Table)[] = [];

  // Page break before peer analysis
  elements.push(
    new Paragraph({
      children: [],
      pageBreakBefore: true,
    })
  );

  // Title
  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: peerAnalysis.report_title,
          bold: true,
          size: 36,
          color: TEAL_COLOR,
          font: DEFAULT_FONT,
        }),
      ],
      spacing: { after: 200 },
    })
  );

  elements.push(
    new Paragraph({
      children: [
        new TextRun({ text: peerAnalysis.sector, font: DEFAULT_FONT }),
      ],
      heading: HeadingLevel.HEADING_3,
      spacing: { after: 100 },
    })
  );

  // Basic info
  elements.push(createLabelValue('Country', peerAnalysis.country));
  elements.push(createLabelValue('Data period', peerAnalysis.data_period));
  elements.push(createLabelValue('Currency', peerAnalysis.currency));
  elements.push(createDivider());

  // Companies analyzed
  elements.push(createHeading('Companies Analyzed', HeadingLevel.HEADING_2));
  peerAnalysis.companies_analyzed.forEach((company) => {
    elements.push(
      createBulletPoint(`${capitalizeWords(company.name)} (${company.short_name})`)
    );
  });
  elements.push(createDivider());

  // Key Metrics Comparison
  elements.push(createHeading('Key Metrics Comparison', HeadingLevel.HEADING_2));

  (Object.values(peerAnalysis.key_metrics_comparison) as MetricData[]).forEach((metric) => {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `${metric.metric_name_en} Market Share`,
            bold: true,
            size: 24,
            font: DEFAULT_FONT,
          }),
        ],
        spacing: { before: 200, after: 100 },
      })
    );

    elements.push(generateKeyMetricsTable(metric.companies));

    elements.push(
      new Paragraph({
        children: [
          new TextRun({ text: 'Industry total: ', bold: true, font: DEFAULT_FONT }),
          new TextRun({ text: `${formatNumber(metric.industry_total)} RSD`, font: DEFAULT_FONT }),
        ],
        spacing: { after: 200 },
      })
    );
  });

  elements.push(createDivider());

  // Market Structure
  elements.push(createHeading('Market Structure Overview', HeadingLevel.HEADING_2));
  elements.push(generateMarketStructureTable(peerAnalysis.key_metrics_comparison));
  elements.push(createDivider());

  // Company Profiles
  elements.push(createHeading('Company Financial Comparison', HeadingLevel.HEADING_2));
  elements.push(generateCompanyProfilesTable(peerAnalysis.company_profiles));
  elements.push(createDivider());

  // Peer Rankings
  elements.push(createHeading('Peer Rankings', HeadingLevel.HEADING_2));

  (Object.entries(peerAnalysis.peer_rankings) as [string, string[]][]).forEach(([key, ranking]) => {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `${capitalizeWords(key.replace(/_/g, ' '))}:`,
            bold: true,
            font: DEFAULT_FONT,
          }),
        ],
        spacing: { before: 100, after: 50 },
      })
    );

    ranking.forEach((company, index) => {
      elements.push(createNumberedItem(capitalizeWords(company), index));
    });
  });

  elements.push(createDivider());

  // Analysis Narrative
  if (peerAnalysis.analysis_narrative_md) {
    elements.push(createHeading('Analysis Narrative', HeadingLevel.HEADING_2));
    const narrativeLines = peerAnalysis.analysis_narrative_md
      .replace(/#{1,6}\s/g, '')
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .split('\n')
      .filter((line) => line.trim());

    narrativeLines.forEach((line) => {
      elements.push(
        new Paragraph({
          children: [
            new TextRun({ text: line.trim(), font: DEFAULT_FONT }),
          ],
          spacing: { after: 100 },
        })
      );
    });
    elements.push(createDivider());
  }

  // Key Findings
  elements.push(createHeading('Key Findings', HeadingLevel.HEADING_2));
  peerAnalysis.key_findings.forEach((finding, index) => {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `Finding ${index + 1} (${finding.significance}):`,
            bold: true,
            color: TEAL_COLOR,
            font: DEFAULT_FONT,
          }),
        ],
        spacing: { before: 150, after: 50 },
      })
    );

    elements.push(
      new Paragraph({
        children: [
          new TextRun({ text: finding.finding, font: DEFAULT_FONT }),
        ],
        spacing: { after: 50 },
      })
    );

    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `Companies affected: ${finding.companies_affected.join(', ')}`,
            italics: true,
            size: 20,
            font: DEFAULT_FONT,
          }),
        ],
        spacing: { after: 100 },
      })
    );
  });

  elements.push(createDivider());

  // Limitations
  elements.push(createHeading('Limitations', HeadingLevel.HEADING_2));
  peerAnalysis.limitations.forEach((limitation) => {
    elements.push(createBulletPoint(limitation));
  });

  return elements;
};

export const generateClientPositionDocx = async (
  report: ClientPositionReport
): Promise<void> => {
  const { market_position, peer_analysis, market_analysis } = report;

  const children: (Paragraph | Table)[] = [];

  // Market Analysis section (if available) - comes first
  if (market_analysis) {
    children.push(...generateMarketAnalysisSection(market_analysis));
  }

  // Market Position section (if available)
  if (market_position){
    children.push(...generateMarketPositionSection(market_position));
  }

  // Peer Analysis section (if available)
  if (peer_analysis) {
    children.push(...generatePeerAnalysisSection(peer_analysis));
  }

  const doc = new Document({
    sections: [
      {
        properties: {},
        children,
      },
    ],
  });

  const blob = await Packer.toBlob(doc);
  const fileName = market_position ? `${market_position?.client_name.replace(/\s+/g, '_')}_Client_Position_Report.docx` : "Market_Analysis_Document.docx";
  saveAs(blob, fileName);
};

export default generateClientPositionDocx;
