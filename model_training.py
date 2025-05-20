import argparse
import io
import os
import time

import boto3
import pandas as pd
import tensorflow_probability as tfp


from meridian import constants
from meridian.data import load
from meridian.model import model
from meridian.model import spec
from meridian.model import prior_distribution
from meridian.analysis import visualizer, summarizer, optimizer

from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Обработка файла')
    parser.add_argument('--path', type=str, required=True, help='Путь к файлу CSV')
    args = parser.parse_args()
    s3_filename = args.path
    print("Путь к файлу:", args.path)
    AWS_ACCESS_KEY_ID = 'YCAJEijNceD5AzHqkfDRopjcJ'
    AWS_SECRET_ACCESS_KEY = 'YCOD_LupG-ynCGilC49OFkJNAtePVayxh1YkoTvI'
    # s3_filename = '1747297675.641256_geo_all_channels (1).csv'

    session = boto3.session.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name='ru-central1'
    )
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

    obj = s3.get_object(Bucket='google-meridian', Key=s3_filename)
    obj_data = obj.get('Body').read()
    df = pd.read_csv(io.BytesIO(obj_data))
    print(df)

    coord_to_columns = load.CoordToColumns(
        time='time',
        geo='geo',
        controls=['GQV', 'Competitor_Sales'],
        population='population',
        kpi='conversions',
        revenue_per_kpi='revenue_per_conversion',
        media=[
            'Channel0_impression',
            'Channel1_impression',
            'Channel2_impression',
            'Channel3_impression',
            'Channel4_impression',
        ],
        media_spend=[
            'Channel0_spend',
            'Channel1_spend',
            'Channel2_spend',
            'Channel3_spend',
            'Channel4_spend',
        ],
        organic_media=['Organic_channel0_impression'],
        non_media_treatments=['Promo'],
    )

    correct_media_to_channel = {
        'Channel0_impression': 'Channel_0',
        'Channel1_impression': 'Channel_1',
        'Channel2_impression': 'Channel_2',
        'Channel3_impression': 'Channel_3',
        'Channel4_impression': 'Channel_4',
    }
    correct_media_spend_to_channel = {
        'Channel0_spend': 'Channel_0',
        'Channel1_spend': 'Channel_1',
        'Channel2_spend': 'Channel_2',
        'Channel3_spend': 'Channel_3',
        'Channel4_spend': 'Channel_4',
    }

    loader = load.DataFrameDataLoader(
        df=df,
        kpi_type='non_revenue',
        coord_to_columns=coord_to_columns,
        media_to_channel=correct_media_to_channel,
        media_spend_to_channel=correct_media_spend_to_channel,
    )
    data = loader.load()

    roi_mu = 0.2     # Mu for ROI prior for each media channel.
    roi_sigma = 0.9  # Sigma for ROI prior for each media channel.
    prior = prior_distribution.PriorDistribution(
        roi_m=tfp.distributions.LogNormal(roi_mu, roi_sigma, name=constants.ROI_M)
    )
    model_spec = spec.ModelSpec(prior=prior)

    mmm = model.Meridian(input_data=data, model_spec=model_spec)
    print(f'{mmm=}')

    mmm.sample_prior(200)
    mmm.sample_posterior(n_chains=2, n_adapt=100, n_burnin=100, n_keep=100, seed=1)
    print('END', 50 * '-----------')

    media_summary = visualizer.MediaSummary(mmm)
    result_data = media_summary.summary_table()
    print(result_data)

    csv_buffer = io.StringIO()
    result_data.to_csv(csv_buffer, index=False, header=True)
    s3.put_object(Body=csv_buffer.getvalue(), Bucket='google-meridian', Key=f'RESULT_{s3_filename}')
    print('save to s3')

    local_report_path = 'summary_output.html'
    mmm_summarizer = summarizer.Summarizer(mmm)
    filepath = 'app/'
    start_date = '2021-01-25'
    end_date = '2024-01-15'
    mmm_summarizer.output_model_results_summary(local_report_path, filepath, start_date, end_date)
    time.sleep(10)

    s3.upload_file(
        Filename=f'{filepath}{local_report_path}',
        Bucket='google-meridian',
        Key=f'{s3_filename}_{local_report_path}'
    )
    print('основной отчет готов и сохранен')

    local_report_budget_path = 'optimization_output.html'
    budget_optimizer = optimizer.BudgetOptimizer(mmm)
    optimization_results = budget_optimizer.optimize()
    filepath = 'app/'
    optimization_results.output_optimization_summary(local_report_budget_path, filepath)
    time.sleep(10)

    s3.upload_file(
        Filename=f'{filepath}{local_report_budget_path}',
        Bucket='google-meridian',
        Key=f'{s3_filename}_{local_report_budget_path}'
    )
    print('отчет по бюджету готов и сохранен')

    os.remove(f'{filepath}{local_report_path}')
    os.remove(f'{filepath}{local_report_budget_path}')
