import { Component, OnDestroy, OnInit } from '@angular/core';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { BrowserModule } from '@angular/platform-browser';
import {ApiService} from '../../shared/api/api.service';
import {Visit} from '../../shared/models';

@Component({
  selector: 'app-user-graph',
  templateUrl: './user-graph.component.html',
  styleUrls: ['./user-graph.component.scss'],
})
export class UserGraphComponent implements OnInit, OnDestroy {
  constructor(
    private api: ApiService
  ) {}

  // todo handle error better?
  // todo slider labels...?

  errorMessage: string;
  startTime: number;
  endTime: number;

  visits: any;

  ngOnInit(): void {
    // default start time is 7 days ago
    let dt = new Date()
    dt.setDate(dt.getDate() - 7);
    this.startTime = dt.getTime();

    // end time is always now
    this.endTime = Date.now();
    this.getVisits(this.startTime, this.endTime);
    this.startTime = -7;
  }


  onSliderChange(value: number) {
    setTimeout(() => {
      if (value == this.startTime) {
        let d = new Date();
        d.setDate(d.getDate() + value);
        this.getVisits(d.getTime(), this.endTime);
      }
    }, 500)
  }


  /* gets all visits in a certain period */
  getVisits(startTime: number, endTime: number) {
    this.api.getVisitors({
      start_date: startTime,
      end_date: endTime
    }).subscribe((res) => {
      let data = res['visits'];
      if (data === undefined) { // for backward compatibility
        data = res['visitors'];
      }
      this.visits = this.convertData(data, startTime, endTime);
    }, (err) => {
      this.errorMessage = err.message;
    });
  }


  /* converts response to usable data */
  convertData(data: Visit[], startTime: number, endTime: number) {

    let interval = endTime - startTime;
    let stepSize = 1000 * 60 * 60 * 24; // a day
    let steps = Math.floor(interval / stepSize);

    let ret = [{
      name: 'All Users',
      series: []
    }, {
      name: 'New Users',
      series: []
    }
    ]; // return data
    let t = startTime;
    for (let i = 0; i < steps; i++) {
      let series = [];
      t += stepSize;
      let count = {
        'new': 0,
        'all': 0,
      }
      for (const visit of (data as any)) {
        let d = visit.date_visited;
        if (t[0] >= d && d <= t[1]) {
          count[d.is_new ? 'new' : 'all']++;
        }
      }
      ret[0].series.push({'name': i, 'value': count['all']});
      ret[1].series.push({'name': i, 'value': count['new']});
    }

    return ret;
  }

  /* exports users data to csv file */
  exportUserData() {
    let rowDelimiter = '\n';
    let columnDelimiter = ',';
    let formattedData = 'data:text/csv;charset=utf-8,';

    //setup header of csv as All Users, New Users, Day
    formattedData += 'Day' + columnDelimiter;
    this.visits.forEach(function (item, index) {
      formattedData += item.firstName + columnDelimiter;
    });
    formattedData = formattedData.slice(0, -1) + rowDelimiter; //replace last comma with newline

    let temp = this.visits[1];
    //for each day listed in the series, record data
    this.visits[0].series.forEach(function (item, index) {
      formattedData +=
        item.firstName +
        columnDelimiter +
        item.value +
        columnDelimiter +
        temp.series[index].value +
        rowDelimiter;
    });

    //Download data as a csv
    let encodedUri = encodeURI(formattedData);
    var link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'Users.csv');
    link.id = 'csv-dl';
    document.body.appendChild(link);
    link.click();
  }

  /* remove csv link on leaving page */
  ngOnDestroy() {
    let csv = document.getElementById("csv-dl")
      if (csv){csv.remove()}
  }
}
