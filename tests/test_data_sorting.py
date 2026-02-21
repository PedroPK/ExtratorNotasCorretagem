"""
Testes para ordenação de dados (Secondary Sorting v1.1)
Valida que dados são ordenados primeiro por Data, depois por Ticker
"""

import pytest
import pandas as pd
from datetime import datetime


class TestDataSorting:
    """Testa ordenação primária por Data"""
    
    def test_data_sorted_ascending(self, sample_unsorted_dataframe):
        """Dados devem estar ordenados por Data em ordem ascendente"""
        df = sample_unsorted_dataframe.copy()
        
        # Aplica ordenação: Data + Ticker
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        # Verifica que está em ordem ascendente
        dates = df['Data'].tolist()
        for i in range(len(dates) - 1):
            assert dates[i] <= dates[i + 1], f"Ordem de datas incorreta: {dates[i]} > {dates[i + 1]}"
    
    def test_oldest_date_first(self, sample_unsorted_dataframe):
        """Data mais antiga deve estar primeiro"""
        df = sample_unsorted_dataframe.copy()
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        first_date = df['Data'].iloc[0]
        assert first_date == pd.to_datetime('2018-10-03'), "Data mais antiga deveria ser primeira"
    
    def test_newest_date_last(self, sample_unsorted_dataframe):
        """Data mais recente deve estar por último"""
        df = sample_unsorted_dataframe.copy()
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        last_date = df['Data'].iloc[-1]
        assert last_date == pd.to_datetime('2018-11-23'), "Data mais recente deveria ser última"


class TestSecondarySorting:
    """Testa ordenação secundária por Ticker"""
    
    def test_ticker_sorted_within_same_date(self):
        """Tickers devem estar em ordem alfabética dentro da mesma Data"""
        data = {
            'Data': ['03/10/2018', '03/10/2018', '03/10/2018', '03/10/2018'],
            'Ticker': ['SUZB3', 'FORJ3', 'XXXX3', 'AAAA3'],
            'Preço': ['44.00', '5.02', '10.00', '20.00']
        }
        df = pd.DataFrame(data)
        
        # Ordena por Data + Ticker
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df_sorted = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        # Verifica ordem de tickers na mesma data
        tickers = df_sorted['Ticker'].tolist()
        expected = ['AAAA3', 'FORJ3', 'SUZB3', 'XXXX3']
        assert tickers == expected, f"Ordem de tickers incorreta: {tickers}"
    
    def test_multiple_dates_with_sorted_tickers(self, sample_unsorted_dataframe):
        """Cada data deve ter seus tickers em ordem alfabética"""
        df = sample_unsorted_dataframe.copy()
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        # Agrupa por data e verifica tickers dentro de cada grupo
        for date, group in df.groupby('Data'):
            tickers = group['Ticker'].tolist()
            # Verifica que tickers estão em ordem dentro dessa data
            assert tickers == sorted(tickers), f"Tickers não estão em ordem na data {date}"


class TestCombinedSorting:
    """Testa combinação de ordenação: Data + Ticker"""
    
    def test_sort_order_is_data_then_ticker(self):
        """Resultado final deve ter Data como primária e Ticker como secundária"""
        data = {
            'Data': ['05/10/2018', '03/10/2018', '05/10/2018', '03/10/2018'],
            'Ticker': ['ZZZA', 'TTTB', 'AAAA', 'BBBB'],
        }
        df = pd.DataFrame(data)
        
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        # Verifica sequência esperada
        result = list(zip(df['Data'].dt.strftime('%d/%m/%Y'), df['Ticker']))
        expected = [
            ('03/10/2018', 'BBBB'),
            ('03/10/2018', 'TTTB'),
            ('05/10/2018', 'AAAA'),
            ('05/10/2018', 'ZZZA'),
        ]
        
        assert result == expected, f"Ordem combinada incorreta: {result}"
    
    def test_large_dataset_sorting(self):
        """Teste com dataset maior (simulating real data)"""
        # Simula 180 registros (2018 dataset)
        dates = ['03/10/2018'] * 30 + ['04/10/2018'] * 30 + ['11/09/2018'] * 120
        tickers = ['FORJ3', 'SUZB3', 'BTOW3'] * 60
        
        df = pd.DataFrame({
            'Data': dates,
            'Ticker': tickers,
        })
        
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        # Verifica que Data é primária (primeira linha deve ser 11/09/2018)
        assert df['Data'].iloc[0] == pd.to_datetime('2018-09-11')
        
        # Verifica que dentro de cada data, tickers estão ordenados
        for date, group in df.groupby('Data'):
            tickers = group['Ticker'].tolist()
            assert tickers == sorted(tickers), f"Ordem não respeitada em {date}"


class TestSortingPreservesData:
    """Testa que a ordenação não altera os dados"""
    
    def test_no_data_loss_during_sorting(self, sample_unsorted_dataframe):
        """Sorting não deve perder dados"""
        df_original = sample_unsorted_dataframe.copy()
        original_length = len(df_original)
        
        df_sorted = df_original.copy()
        df_sorted['Data'] = pd.to_datetime(df_sorted['Data'], format='%d/%m/%Y')
        df_sorted = df_sorted.sort_values(['Data', 'Ticker'], ascending=True)
        
        assert len(df_sorted) == original_length, "Linhas foram perdidas durante sorting"
    
    def test_all_values_preserved(self, sample_unsorted_dataframe):
        """Todos os valores devem ser preservados após sorting"""
        df = sample_unsorted_dataframe.copy()
        original_values = set(df['Ticker'].tolist())
        
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        
        sorted_values = set(df['Ticker'].tolist())
        assert original_values == sorted_values, "Valores foram perdidos ou duplicados"


class TestSortingPerformance:
    """Testa performance da ordenação"""
    
    def test_sorting_large_dataset_is_fast(self):
        """Sorting de 10000 registros deve ser rápido"""
        import time
        
        # Cria dataset de 10000 registros com datas válidas (01-31)
        dates = [f"{(i % 31) + 1:02d}/10/2018" for i in range(10000)]
        tickers = ['USIM5', 'VALE3', 'PETR4', 'ITUB4'] * 2500
        
        df = pd.DataFrame({
            'Data': dates,
            'Ticker': tickers,
        })
        
        start = time.time()
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df = df.sort_values(['Data', 'Ticker'], ascending=True)
        elapsed = time.time() - start
        
        # Deve completar em menos de 1 segundo
        assert elapsed < 1.0, f"Sorting muito lento: {elapsed}s para 10000 registros"
