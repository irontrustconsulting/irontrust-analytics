import { AvgEntropyChart } from "../components/charts/AvgEntropyChart";
import { NxDomainChart } from "../components/charts/NxDomainChart";
// import { QnameLengthChart } from "../components/charts/QnameLengthChart";
import { TopDomainsChart } from "../components/charts/TopDomainsChart";
import { TopQueryTypesChart } from "../components/charts/TopQueryTypesChart";
import { TopNClientsChart } from "../components/charts/TopNClientsChart";
import { QnameHistChart } from "../components/charts/QnameHistChart";

export const chartRegistry = {
  avg_entropy: AvgEntropyChart,
  nx_domain: NxDomainChart,
  qname_length: QnameHistChart,
  top_domains: TopDomainsChart,
  top_query_types: TopQueryTypesChart,
  topn_clients: TopNClientsChart
};
