import { useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html, Line, OrbitControls } from "@react-three/drei";
import { feature } from "topojson-client";
import countries from "world-atlas/countries-110m.json";
import * as THREE from "three";

import {
  locationFixtures,
  regionalEffectFixtures,
  type ConsequenceCategory,
} from "../data/presentation";

type GeoFeature = {
  id?: string | number;
  properties?: { name?: string };
  geometry: { type: string; coordinates: unknown };
};

function pointOnGlobe(latitude: number, longitude: number, radius: number) {
  const phi = ((90 - latitude) * Math.PI) / 180;
  const theta = ((longitude + 180) * Math.PI) / 180;
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  );
}

function rings(featureItem: GeoFeature): number[][][] {
  if (featureItem.geometry.type === "Polygon")
    return featureItem.geometry.coordinates as number[][][];
  if (featureItem.geometry.type === "MultiPolygon")
    return (featureItem.geometry.coordinates as number[][][][]).flat();
  return [];
}

function CountryLines({
  highlightedCountries,
}: {
  highlightedCountries: string[];
}) {
  const features = useMemo(() => {
    const topology = countries as unknown as { objects: { countries: object } };
    return (
      feature(
        topology as never,
        topology.objects.countries as never,
      ) as unknown as { features: GeoFeature[] }
    ).features;
  }, []);

  return features.flatMap((country, countryIndex) => {
    const highlighted = highlightedCountries.includes(
      country.properties?.name ?? "",
    );
    return rings(country).map((ring, ringIndex) => (
      <Line
        key={`${countryIndex}-${ringIndex}`}
        points={ring
          .filter((_, index) => index % 2 === 0)
          .map(([longitude, latitude]) =>
            pointOnGlobe(latitude, longitude, 1.006),
          )}
        color={highlighted ? "#f0a94d" : "#57564f"}
        transparent
        opacity={highlighted ? 1 : 0.58}
        lineWidth={highlighted ? 1.4 : 0.45}
      />
    ));
  });
}

function Marker({
  latitude,
  longitude,
  color,
  label,
  cluster = false,
}: {
  latitude: number;
  longitude: number;
  color: string;
  label: string;
  cluster?: boolean;
}) {
  const position = pointOnGlobe(latitude, longitude, 1.04);
  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[cluster ? 0.025 : 0.04, 16, 16]} />
        <meshBasicMaterial color={color} />
      </mesh>
      {!cluster && (
        <Html center distanceFactor={7} className="globe-label">
          <span>{label}</span>
        </Html>
      )}
    </group>
  );
}

function DirectedCamera({
  reducedMotion,
  target,
}: {
  reducedMotion: boolean;
  target: { latitude: number; longitude: number };
}) {
  const destination = useMemo(
    () => pointOnGlobe(target.latitude, target.longitude, 3.05),
    [target.latitude, target.longitude],
  );
  useFrame(({ camera }) => {
    if (!reducedMotion) camera.position.lerp(destination, 0.025);
    camera.lookAt(0, 0, 0);
  });
  return null;
}

export function GlobeScene({
  originLocation,
  reducedMotion,
  activeCategory,
  visibleCategories,
}: {
  originLocation: string;
  reducedMotion: boolean;
  activeCategory: ConsequenceCategory;
  visibleCategories: ConsequenceCategory[];
}) {
  const origin = locationFixtures[originLocation] ?? {
    label: originLocation,
    latitude: 25,
    longitude: 55,
    highlightedCountries: [originLocation],
  };
  const visibleRegions = regionalEffectFixtures.filter((region) =>
    visibleCategories.includes(region.category),
  );
  const cameraTarget =
    visibleRegions.find((region) => region.category === activeCategory) ??
    origin;
  return (
    <div
      className="globe-wrap"
      role="img"
      aria-label={`World map highlighting ${origin.label} and illustrative fixture effect regions`}
    >
      <Canvas
        camera={{ position: [0.8, 0.55, reducedMotion ? 3.05 : 4.4], fov: 42 }}
        dpr={[1, 1.5]}
      >
        <ambientLight intensity={1.2} />
        <directionalLight
          position={[2, 3, 4]}
          intensity={2.5}
          color="#ffd28b"
        />
        <mesh>
          <sphereGeometry args={[1, 64, 64]} />
          <meshStandardMaterial
            color="#171816"
            roughness={0.9}
            metalness={0.15}
          />
        </mesh>
        <CountryLines highlightedCountries={origin.highlightedCountries} />
        <Marker
          latitude={origin.latitude}
          longitude={origin.longitude}
          color="#f0a94d"
          label={origin.label}
        />
        {visibleRegions.map((region) => (
          <Marker key={region.label} {...region} color="#d7a05d" cluster />
        ))}
        <DirectedCamera reducedMotion={reducedMotion} target={cameraTarget} />
        <OrbitControls
          enablePan={false}
          minDistance={2.4}
          maxDistance={4.5}
          autoRotate={!reducedMotion}
          autoRotateSpeed={0.25}
        />
      </Canvas>
      <div className="map-legend">
        <span>
          <i className="origin-dot" /> Event origin
        </span>
        <span>
          <i className="cluster-dot" /> Illustrative fixture region
        </span>
        <small>
          Country context: {origin.highlightedCountries.join(" / ")}
        </small>
      </div>
    </div>
  );
}
