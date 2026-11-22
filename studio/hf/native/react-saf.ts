// Native çekirdeğinde React yok: tema.ts yalnız bağlam (TemaSaglayici/useTema) için React'e dokunur, sahne bunları kullanmaz.
export const createContext = <T,>(v: T) => ({ _v: v, Provider: null as unknown });
export const useContext = <T,>(c: { _v: T }) => c._v;
export const createElement = () => null;
export default { createElement, createContext, useContext };
