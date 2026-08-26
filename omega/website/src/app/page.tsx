import { Hero } from "@/components/home/hero";
import {
  BoundarySection,
  Claims,
  Loop,
  Origin,
  Providers,
  Stack,
  Timeline,
} from "@/components/home/sections";

/**
 * Composition only.
 *
 * The order is the argument: what it is, how it works, how it is split, what
 * that bought, the layers, the providers, where it stands, where it came from.
 * Each section owns its own markup and data, so changing one cannot disturb
 * another — and no section repeats the shape of its neighbour.
 */
export default function Home() {
  return (
    <>
      <Hero />
      <Loop />
      <BoundarySection />
      <Claims />
      <Stack />
      <Providers />
      <Timeline />
      <Origin />
    </>
  );
}
