import { Divider } from '@mui/material';
import { Industry } from '@/src/lib/industries';
import { findNaceLabel } from '@/src/lib/naceCategories';
import Link from 'next/link';

type IndustryOverviewProps = {
  industry: Industry
}

// Shown for industries that don't have a generated market analysis yet
const IndustryOverview = ({ industry }: IndustryOverviewProps) => {

  return (
    <div>
      <div className='flex flex-col gap-1.5'>
        {/* TODO: only Electricity has its own UAF form for now */}
        {industry.id === "electricity" &&
          <Link href="/analysis/new/electricity" className="self-end" prefetch={false}>
            Generiši novi UAF
          </Link>
        }
        <h1>
          {industry.name}
        </h1>
        <h3 className="text-md">Izveštaj o analizi tržišta i cena</h3>

        <p>
          <strong>NACE: </strong>
        </p>
        <ul className="list-disc mx-4">
          {industry.naceCodes.map(code => <li key={code}>{findNaceLabel(code) ?? code}</li>)}
        </ul>

        <p className="text-charcoal-80">
          Analiza za ovu industriju još nije generisana.
        </p>
      </div>

      <Divider />

      {industry.sections.map((section, index) =>
        <div key={section.id} className="flex flex-col gap-3">
          <h3>{section.title}</h3>
          <ul className="list-disc mx-4">
            {section.subsections.map(subsection => <li key={subsection}>{subsection}</li>)}
          </ul>

          {
            index !== industry.sections.length - 1 &&
            <Divider />
          }
        </div>
      )}

      {industry.sections.length === 0 && <p>Za ovu industriju još nisu definisane sekcije.</p>}
    </div>
  )
}

export default IndustryOverview;
