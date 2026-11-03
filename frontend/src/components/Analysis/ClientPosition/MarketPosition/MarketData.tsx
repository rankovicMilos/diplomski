import cn from "@/src/utils/cn"
import { GifBox, InsightsOutlined, Inventory2, Inventory2Outlined, Map, MapOutlined, MonetizationOnOutlined, TrendingUpOutlined } from "@mui/icons-material"
import { Slider } from "@mui/material"

type MarketDataProps = {
  market_data: {
    total_production_tonnes: number | null,
    harvested_area_ha: number | null,
    yield_per_ha: number | null,
    price_data: {
      average_price: number | null,
      price_unit: string,
      price_range_low: number | null,
      price_range_high: number | null
    },
    total_market_value: {
      value: number | null,
      unit: string
    }
  }
}

type DataCardProps = {
  title: string,
  value: string,
  label: string,
  icon: React.ReactNode,
  className?: string
}

const DataCard = ({ title, value, label, icon, className }: DataCardProps) => (
  <div className={cn("flex flex-col gap-2 rounded-md border px-6 py-5 w-[25%]", className)}>
    <div className="flex gap-1">
      {icon}
      <span className="text-xs">
        {title}
      </span>
    </div>
    <div className="flex flex-col ml-1">
      <span className="text-3xl font-bolder">{value}</span>
      <span className="text-2xs">{label}</span>
    </div>
  </div>
)

const MarketData = ({ market_data }: MarketDataProps) => {

  // The LLM returns null for values it couldn't find
  const formatNumber = (num: number | null) => {
    if (num === null || num === undefined) return 'N/D';
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatCurrency = (num: number | null) => {
    if (num === null || num === undefined) return 'N/D';
    if (num >= 1e9) {
      return (num / 1e9).toFixed(1) + 'B';
    }
    if (num >= 1e6) {
      return (num / 1e6).toFixed(1) + 'M';
    }
    return formatNumber(num);
  };

  const { average_price, price_range_low, price_range_high } = market_data.price_data;
  const hasPriceRange = average_price != null && price_range_low != null && price_range_high != null;

  return (
    <div className="flex flex-col gap-2 my-6">
      <h5>Pregled tržišta</h5>

      <div className="flex gap-4">

        {/* total production */}
        <DataCard
          title="Ukupna proizvodnja"
          icon={<Inventory2Outlined />}
          value={formatNumber(market_data.total_production_tonnes)}
          label="tona"
          className="bg-teal-10 border-teal-90"

        />

        {/* harvested area */}
        <DataCard
          title="Požnjevena površina"
          icon={<MapOutlined />}
          value={formatNumber(market_data.harvested_area_ha)}
          label="hektara"
          className="bg-yellow-10 border-yellow-90" />

        {/* Yield per hectare */}
        <DataCard
          title="Prinos po hektaru"
          icon={<TrendingUpOutlined />}
          value={formatNumber(market_data.yield_per_ha)}
          label="tonnes/ha"
          className="bg-green-10 border-green-75" />

        {/* Total market value */}
        <DataCard
          title="Ukupna vrednost tržišta"
          icon={<MonetizationOnOutlined />}
          value={`${formatCurrency(market_data.total_market_value.value)} ${market_data.total_market_value.unit}`}
          label={formatNumber(market_data.total_market_value.value)}
          className="bg-purple-10 border-purple-100" />

      </div>

      {/* price analysis */}

      <div className="flex flex-col gap-2 rounded-md border border-charcoal-100 bg-steel-40 px-6 py-5">
        <div className="flex gap-3">
          <InsightsOutlined />
          <div className="flex flex-col">
            <span className="text-sm">
              Analiza cena
            </span>
            <span className="text-2xs">
              {market_data.price_data.price_unit}
            </span>
          </div>
        </div>

        <div className="text-center my- flex flex-col">
          <span>Prosečna cena</span>
          <span className="text-3xl">{formatNumber(market_data.price_data.average_price)}</span>
          <span className="text-xs">{market_data.price_data.price_unit}</span>
        </div>

        {hasPriceRange && <div className="bg-steel-50 rounded-md px-6 py-2">
          <div className="flex justify-between text-xs mb-2">
            <span className="text-gray-600">Niska</span>
            <span className="text-gray-600">Visoka</span>
          </div>
          <Slider
            aria-label="Podaci o ceni"
            value={average_price}
            min={price_range_low}
            max={price_range_high}
            disabled
            marks={[
              { value: price_range_low, label: '' },
              { value: average_price, label: '' },
              { value: price_range_high, label: '' }
            ]}
            sx={{
              '& .MuiSlider-thumb': {
                backgroundColor: '#1976d2',
                width: 16,
                height: 16,
                '&:hover, &.Mui-focusVisible': {
                  boxShadow: '0 0 0 8px rgba(25, 118, 210, 0.16)',
                },
              },
              '& .MuiSlider-track': {
                backgroundColor: '#1976d2',
                height: 6,
              },
              '& .MuiSlider-rail': {
                backgroundColor: '#e0e0e0',
                height: 6,
              },
              '& .MuiSlider-mark': {
                backgroundColor: '#bdbdbd',
                height: 12,
                width: 2,
              },
              '&.Mui-disabled': {
                color: '#1976d2',
              },
            }}
          />
          <div className="flex justify-between text-sm font-medium mt-1">
            <span>{formatNumber(market_data.price_data.price_range_low)}</span>
            <span className="text-blue-600 font-bold">
              {formatNumber(market_data.price_data.average_price)}
            </span>
            <span>{formatNumber(market_data.price_data.price_range_high)}</span>
          </div>
        </div>}
      </div>
    </div>
  )
}
export default MarketData;