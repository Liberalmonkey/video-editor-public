// cli.ts paketinde gerçek "remotion" paketine çözülür (taklit modül kendi adını kullanamaz).
declare module "remotion-gercek" {
  export * from "remotion";
}
