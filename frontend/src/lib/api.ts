import { UploadedFile } from "../components/DragAndDropFile/DragAndDropFile";
import { API_PROXY_PATH, API_URL } from "./apiUrl";

export type ResponseType<T> = Promise<{
  status: number;
  data: T;
}>;

export interface IMarketAnalysis {
  analysis_id: string,
  job_id: string,
  status: string,
  language: string,
  generated_at: string,
  meta: {
    sector: string,
    country: string,
    period: string
  },
  sections: {
    id: string,
    title: string,
    order: number,
    content_md: string
    tableId?: string
  }[],
  tables: {
    id: string,
    title: string,
    columns: {
      id: string,
      name: string,
      type: string
    }[],
    rows: (string | number | null)[][]
  }[],
  charts: {
    id: string,
    title: string,
    type: string,
    data: {
      label: string,
      value: number
    }[]
  }[],
  sources: {
    name: string,
    date: string
  }[]
}

export interface IMarketDataSummary {
    commodity: string,
    total_production_tonnes: number,
    harvested_area_ha: number,
    price_data: {
      average_price: number,
      price_unit: string,
      price_range_low?: number,
      price_range_high?: number
    },
    total_market_value: {
      value: number,
      unit: string
    }
  } 


export interface IMarketPositionReport {
  nace_code?: string,
  analysis_id: string,
  market_analysis_id: string,
  client_name: string,
  analysis_period: string,
  currency: string,
  client_financials_summary: {
    total_revenue: {
      value: number,
      unit: string,
      scale_applied: string,
      year: number
    },
    revenue_trend: string
  },
  commodities_analyzed: {
      commodity: string,
      revenue_share_pct: number,
      estimated_revenue: {
        value: number,
        unit: string
      },
      market_data: {
        total_production_tonnes: number,
        harvested_area_ha: number,
        yield_per_ha: number,
        price_data: {
          average_price: number,
          price_unit: string,
          price_range_low: number,
          price_range_high: number
        },
        total_market_value: {
          value: number,
          unit: string
        }
      },
      // ComodityData
      estimated_volume: {
        low_estimate_tonnes: number,
        mid_estimate_tonnes: number,
        high_estimate_tonnes: number
      },
      market_share: {
        low_estimate_pct: number,
        mid_estimate_pct: number,
        high_estimate_pct: number
      }
    }[],
  weighted_market_position: {
    methodology: string,
    weighted_market_share: {
      low_estimate_pct: number,
      mid_estimate_pct: number,
      high_estimate_pct: number
    },
    calculation_basis: string
  },
  market_position_analysis: {
    methodology: string,
    assumptions: string[],
  },
  analysis_narrative_md: string; 
  tables: {
    id: string,
    title: string,
    columns: {
      id: string,
      name: string,
      type: string
    }[],
    rows: (string | number | null)[][]
  }[],
  charts: {
    id: string,
    title: string,
    type: string,
    y_axis_unit?: string,
    data: {
      label: string,
      value: number
    }[]
  }[],
  limitations_and_caveats: string[],
  sources: {
      name: string,
      type: string
  }[]
}

export interface IPeerAnalysis {
  analysis_id: string,
  market_position_id: string,
  report_title: string,
  sector: string,
  country: string,
  currency: string,
  data_period: string,
  companies_analyzed: {
    name: string,
    short_name: string
  }[],
  key_metrics_comparison: {
    total_assets: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
          name: string,
          value: number,
          market_share_pct: number,
          rank: number
      }[],
      industry_total: number
    },
    total_revenue: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
          name: string,
          value: number,
          market_share_pct: number,
          rank: number
      }[],
      industry_total: number
    },
    operating_revenue: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
          name: string,
          value: number,
          market_share_pct: number,
          rank: number
      }[],
      industry_total: number
    },
    revenue_from_goods: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
          name: string,
          value: number,
          market_share_pct: number,
          rank: number
      }[],
      industry_total: number
    },
    revenue_from_products_services: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
          name: string,
          value: number,
          market_share_pct: number,
          rank: number
      }[],
      industry_total: number
    },
    total_expenses: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
          name: string,
          value: number,
          market_share_pct: number,
          rank: number
      }[],
      industry_total: number
    }
  },
  company_profiles: {
      name: string,
      total_assets: number,
      total_revenue: number,
      operating_revenue: number,
      revenue_from_goods: number,
      revenue_from_products_services: number,
      total_expenses: number,
      operating_result: number,
      revenue_mix: {
        goods_pct: number,
        products_services_pct: number
      },
      operating_margin_pct: number,
      asset_turnover: number
  }[],
  peer_rankings: {
    by_total_assets: string[],
    by_total_revenue: string[],
    by_operating_margin: string[]
  },
  analysis_narrative_md: string,
  key_findings: {
      finding: string,
      companies_affected: string[],
      significance: string
  }[],
  limitations: string[]
}

interface IClientReport {
  market_position: IMarketPositionReport,
  peer_analysis: IPeerAnalysis | null
}

interface IMarketPositionsResponse {
  files: {
    key: string,
    filename: string,
    last_modified: string,
    size: number,
    content: {
      analysis_id: string,
      market_analysis_id: string,
      client_name: string,
      nace_code?: string
    }
  }[],
  count: number,
  bucket: string,
  prefix: string
}

export interface MarketPositionRequestBody {
  analysis_id: string,
  analysis_type: string,
  client_data_key?: string,
  client_name: string,
  nace_code: string,
  commodities: {
    name: string,
    revenue_pct: number
  }[],
  primary_currency: string,
  fx_rate_eur_rsd: number,
  fx_rate_date: string
}

interface UploadPdfResponse {
  key: string,
  bucket: string
}

const mapToResponse = async (res: Response) => {
	if (res.status === 204) {
		// No res body
		return { status: res.status, data: null };
	}
	try {
		const data = await res.json();
		return { status: res.status, data };
	} catch (error) {
		return { status: res.status, data: {message: error} };
	}
};

const BASE_URL = process.env.NODE_ENV === "development" ? API_PROXY_PATH : API_URL;

export type GetMarketPositionsQueryParams = {
  clientName?: string | undefined,
  category?: string | undefined
}

export async function getMarketPositions ({clientName, category}: GetMarketPositionsQueryParams): ResponseType<IMarketPositionsResponse> {

  const queryParamsList = []
  if (clientName) queryParamsList.push(`clientName=${encodeURIComponent(clientName)}`)
  if (category) queryParamsList.push(`category=${encodeURIComponent(category)}`) 
  const queryParams = queryParamsList.length ? `?${queryParamsList.join("&")}` : ''
  const res = await fetch(`${BASE_URL}/analyses${queryParams}`);
  return mapToResponse(res)

}

export async function getAnalysisForCategory (category?: string): ResponseType<IMarketAnalysis> {

  const res = await fetch(`${BASE_URL}/analyses/${category}`);
  return mapToResponse(res)

}

export async function getClientAnalysis (marketPositionId: string): ResponseType<IClientReport> {

  const res = await fetch(`${BASE_URL}/analyses/client/${marketPositionId}`);
  return mapToResponse(res)

}

export async function uploadSheetFile (fileName: string, base64: string ) {
  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: JSON.stringify({
      filename: fileName,
      file_content: base64
    })
  });
  return mapToResponse(res)
}

export async function uploadPdfFile (file: UploadedFile): ResponseType<UploadPdfResponse>  {
  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
    })
  });

  if (res.status === 200) {
    const mappedRes = await mapToResponse(res);
    const timestampMatch = mappedRes.data.key.match(/(\d{8}_\d{6})/);
    const uploadTimestamp = timestampMatch ? timestampMatch[1] : '';

    const s3UploadRes = await fetch(mappedRes.data.upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/pdf',
        'x-amz-meta-original_filename': file.name,
        'x-amz-meta-upload_timestamp': uploadTimestamp
      },
      body: file.file
    });

    // Return both the S3 response status and the key for use in subsequent API calls
    return {
      status: s3UploadRes.status,
      data: {
        key: mappedRes.data.key,
        bucket: mappedRes.data.bucket
      }
    }
  }
  return mapToResponse(res)

}

export async function generateMarketPosition (body: MarketPositionRequestBody) {
  const res = await fetch(`${BASE_URL}/analyses`, {
    method: "POST",
    body: JSON.stringify(body)
  });
  return mapToResponse(res)
}